from discord.ext import commands
from modules.utils.dataIO import dataIO
from modules.utils import checks
from modules.utils.chatformat import pagify, box
from __main__ import send_cmd_help, set_module
import os
from subprocess import run as sp_run, PIPE
import shutil
from asyncio import as_completed
from setuptools import distutils
import discord
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from time import time
from importlib.util import find_spec
from copy import deepcopy

NUM_THREADS = 4
REPO_NONEX = 0x1
REPO_CLONE = 0x2
REPO_SAME = 0x4
REPOS_LIST = "https://twentysix26.github.io/Red-Docs/red_cog_approved_repos/"
WINDOWS_OS = os.name == 'nt'

DISCLAIMER = ("You're about to add a 3rd party repository. The creator of ProjectPython"
              " and its community have no responsibility for any potential "
              "damage that the content of 3rd party repositories might cause."
              "\nBy typing 'I agree' you declare to have read and understand "
              "the above message. This message won't be shown again until the"
              " next reboot.")


class UpdateError(Exception):
    pass


class CloningError(UpdateError):
    pass


class RequirementFail(UpdateError):
    pass


class Downloader:
    """Module downloader/installer."""

    def __init__(self, bot):
        self.bot = bot
        self.disclaimer_accepted = False
        self.path = os.path.join("data", "downloader")
        self.file_path = os.path.join(self.path, "repos.json")
        # {name:{url,module1:{installed},module1:{installed}}}
        self.repos = dataIO.load_json(self.file_path)
        self.executor = ThreadPoolExecutor(NUM_THREADS)
        self._do_first_run()

    def save_repos(self):
        dataIO.save_json(self.file_path, self.repos)

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def module(self, ctx):
        """Additional modules management"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @module.group(pass_context=True)
    async def repo(self, ctx):
        """Repo management commands"""
        if ctx.invoked_subcommand is None or \
                isinstance(ctx.invoked_subcommand, commands.Group):
            await send_cmd_help(ctx)
            return

    @repo.command(name="add", pass_context=True)
    async def _repo_add(self, ctx, repo_name: str, repo_url: str):
        """Adds repo to available repo lists

        Warning: Adding 3RD Party Repositories is at your own
        Risk."""
        if not self.disclaimer_accepted:
            await self.bot.say(DISCLAIMER)
            answer = await self.bot.wait_for_message(timeout=30,
                                                     author=ctx.message.author)
            if answer is None:
                await self.bot.say('Not adding repo.')
                return
            elif "i agree" not in answer.content.lower():
                await self.bot.say('Not adding repo.')
                return
            else:
                self.disclaimer_accepted = True
        self.repos[repo_name] = {}
        self.repos[repo_name]['url'] = repo_url
        try:
            self.update_repo(repo_name)
        except CloningError:
            await self.bot.say("That repository link doesn't seem to be "
                               "valid.")
            del self.repos[repo_name]
            return
        except FileNotFoundError:
            error_message = ("I couldn't find git. The downloader needs it "
                             "for it to properly work.")
            if WINDOWS_OS:
                error_message += ("\nIf you just installed it you may need "
                                  "a reboot for it to be seen into the PATH "
                                  "environment variable.")
            await self.bot.say(error_message)
            return
        self.populate_list(repo_name)
        self.save_repos()
        data = self.get_info_data(repo_name)
        if data:
            msg = data.get("INSTALL_MSG")
            if msg:
                await self.bot.say(msg[:2000])
        await self.bot.say("Repo '{}' added.".format(repo_name))

    @repo.command(name="remove")
    async def _repo_del(self, repo_name: str):
        """Removes repo from repo list. MODULES ARE NOT REMOVED."""
        def remove_readonly(func, path, excinfo):
            os.chmod(path, 0o755)
            func(path)

        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        del self.repos[repo_name]
        try:
            shutil.rmtree(os.path.join(self.path, repo_name), onerror=remove_readonly)
        except FileNotFoundError:
            pass
        self.save_repos()
        await self.bot.say("Repo '{}' removed.".format(repo_name))

    @module.command(name="list")
    async def _send_list(self, repo_name=None):
        """Lists installable modules

        Repositories list:
        https://twentysix26.github.io/Red-Docs/red_cog_approved_repos/"""
        retlist = []
        if repo_name and repo_name in self.repos:
            msg = "Available modules:\n"
            for module in sorted(self.repos[repo_name].keys()):
                if 'url' == module:
                    continue
                data = self.get_info_data(repo_name, module)
                if data and data.get("HIDDEN") is True:
                    continue
                if data:
                    retlist.append([module, data.get("SHORT", "")])
                else:
                    retlist.append([module, ''])
        else:
            if self.repos:
                msg = "Available repos:\n"
                for repo_name in sorted(self.repos.keys()):
                    data = self.get_info_data(repo_name)
                    if data:
                        retlist.append([repo_name, data.get("SHORT", "")])
                    else:
                        retlist.append([repo_name, ""])
            else:
                await self.bot.say("You haven't added a repository yet.\n"
                                   "Start now! {}".format(REPOS_LIST))
                return

        col_width = max(len(row[0]) for row in retlist) + 2
        for row in retlist:
            msg += "\t" + "".join(word.ljust(col_width) for word in row) + "\n"
        msg += "\nRepositories list: {}".format(REPOS_LIST)
        for page in pagify(msg, delims=['\n'], shorten_by=8):
            await self.bot.say(box(page))

    @module.command()
    async def info(self, repo_name: str, module: str=None):
        """Shows info about the specified module"""
        if module is not None:
            modules = self.list_modules(repo_name)
            if module in modules:
                data = self.get_info_data(repo_name, module)
                if data:
                    msg = "{} by {}\n\n".format(module, data["AUTHOR"])
                    msg += data["NAME"] + "\n\n" + data["DESCRIPTION"]
                    await self.bot.say(box(msg))
                else:
                    await self.bot.say("The specified module has no info file.")
            else:
                await self.bot.say("That module doesn't exist."
                                   " Use module list to see the full list.")
        else:
            data = self.get_info_data(repo_name)
            if data is None:
                await self.bot.say("That repo does not exist or the"
                                   " information file is missing for that repo"
                                   ".")
                return
            name = data.get("NAME", None)
            name = repo_name if name is None else name
            author = data.get("AUTHOR", "Unknown")
            desc = data.get("DESCRIPTION", "")
            msg = ("```{} by {}```\n\n{}".format(name, author, desc))
            await self.bot.say(msg)

    @module.command(hidden=True)
    async def search(self, *terms: str):
        """Search installable modules"""
        pass  # TO DO

    @module.command(pass_context=True)
    async def update(self, ctx):
        """Updates modules"""

        tasknum = 0
        num_repos = len(self.repos)

        min_dt = 0.5
        burst_inc = 0.1/(NUM_THREADS)
        touch_n = tasknum
        touch_t = time()

        def regulate(touch_t, touch_n):
            dt = time() - touch_t
            if dt + burst_inc*(touch_n) > min_dt:
                touch_n = 0
                touch_t = time()
                return True, touch_t, touch_n
            return False, touch_t, touch_n + 1

        tasks = []
        for r in self.repos:
            task = partial(self.update_repo, r)
            task = self.bot.loop.run_in_executor(self.executor, task)
            tasks.append(task)

        base_msg = "Downloading updated modules, please wait... "
        status = ' %d/%d repos updated' % (tasknum, num_repos)
        msg = await self.bot.say(base_msg + status)

        updated_modules = []
        new_modules = []
        deleted_modules = []
        failed_modules = []
        error_repos = {}
        installed_updated_modules = []

        for f in as_completed(tasks):
            tasknum += 1
            try:
                name, updates, oldhash = await f
                if updates:
                    if type(updates) is dict:
                        for k, l in updates.items():
                            tl = [(name, c, oldhash) for c in l]
                            if k == 'A':
                                new_modules.extend(tl)
                            elif k == 'D':
                                deleted_modules.extend(tl)
                            elif k == 'M':
                                updated_modules.extend(tl)
            except UpdateError as e:
                name, what = e.args
                error_repos[name] = what
            edit, touch_t, touch_n = regulate(touch_t, touch_n)
            if edit:
                status = ' %d/%d repos updated' % (tasknum, num_repos)
                msg = await self._robust_edit(msg, base_msg + status)
        status = 'done. '

        for t in updated_modules:
            repo, module, _ = t
            if self.repos[repo][module]['INSTALLED']:
                try:
                    await self.install(repo, module,
                                       no_install_on_reqs_fail=False)
                except RequirementFail:
                    failed_modules.append(t)
                else:
                    installed_updated_modules.append(t)

        for t in updated_modules.copy():
            if t in failed_modules:
                updated_modules.remove(t)

        if not any(self.repos[repo][module]['INSTALLED'] for
                   repo, module, _ in updated_modules):
            status += ' No updates to apply. '

        if new_modules:
            status += '\nNew modules: ' \
                   + ', '.join('%s/%s' % c[:2] for c in new_modules) + '.'
        if deleted_modules:
            status += '\nDeleted modules: ' \
                   + ', '.join('%s/%s' % c[:2] for c in deleted_modules) + '.'
        if updated_modules:
            status += '\nUpdated modules: ' \
                   + ', '.join('%s/%s' % c[:2] for c in updated_modules) + '.'
        if failed_modules:
            status += '\nModules that got new requirements which have ' + \
                   'failed to install: ' + \
                   ', '.join('%s/%s' % c[:2] for c in failed_modules) + '.'
        if error_repos:
            status += '\nThe following repos failed to update: '
            for n, what in error_repos.items():
                status += '\n%s: %s' % (n, what)

        msg = await self._robust_edit(msg, base_msg + status)

        if not installed_updated_modules:
            return

        patchnote_lang = 'Prolog'
        shorten_by = 8 + len(patchnote_lang)
        for note in self.patch_notes_handler(installed_updated_modules):
            if note is None:
                continue
            for page in pagify(note, delims=['\n'], shorten_by=shorten_by):
                await self.bot.say(box(page, patchnote_lang))

        await self.bot.say("Modules updated. Reload updated modules? (yes/no)")
        answer = await self.bot.wait_for_message(timeout=15,
                                                 author=ctx.message.author)
        if answer is None:
            await self.bot.say("Ok then, you can reload modules with"
                               " `{}reload <module_name>`".format(ctx.prefix))
        elif answer.content.lower().strip() == "yes":
            registry = dataIO.load_json(os.path.join("data", "projectpython", "modules.json"))
            update_list = []
            fail_list = []
            for repo, module, _ in installed_updated_modules:
                if not registry.get('modules.' + module, False):
                    continue
                try:
                    self.bot.unload_extension("modules." + cmoduleog)
                    self.bot.load_extension("modules." + module)
                    update_list.append(module)
                except:
                    fail_list.append(module)
            msg = 'Done.'
            if update_list:
                msg += " The following modules were reloaded: "\
                    + ', '.join(update_list) + "\n"
            if fail_list:
                msg += " The following modules failed to reload: "\
                    + ', '.join(fail_list)
            await self.bot.say(msg)

        else:
            await self.bot.say("Ok then, you can reload modules with"
                               " `{}reload <module_name>`".format(ctx.prefix))

    def patch_notes_handler(self, repo_module_hash_pairs):
        for repo, module, oldhash in repo_module_hash_pairs:
            repo_path = os.path.join('data', 'downloader', repo)
            modulefile = os.path.join(module, module + ".py")
            cmd = ["git", "-C", repo_path, "log", "--relative-date",
                   "--reverse", oldhash + '..', modulefile
                   ]
            try:
                log = sp_run(cmd, stdout=PIPE).stdout.decode().strip()
                yield self.format_patch(repo, module, log)
            except:
                pass

    @module.command(pass_context=True)
    async def uninstall(self, ctx, repo_name, module):
        """Uninstalls a module"""
        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        if module not in self.repos[repo_name]:
            await self.bot.say("That module isn't available from that repo.")
            return
        set_module("modules." + module, False)
        self.repos[repo_name][module]['INSTALLED'] = False
        self.save_repos()
        os.remove(os.path.join("modules", module + ".py"))
        owner = self.bot.get_module('Owner')
        await owner.unload.callback(owner, module_name=module)
        await self.bot.say("Module successfully uninstalled.")

    @module.command(name="install", pass_context=True)
    async def _install(self, ctx, repo_name: str, module: str):
        """Installs specified module"""
        if repo_name not in self.repos:
            await self.bot.say("That repo doesn't exist.")
            return
        if module not in self.repos[repo_name]:
            await self.bot.say("That module isn't available from that repo.")
            return
        data = self.get_info_data(repo_name, module)
        try:
            install_module = await self.install(repo_name, module, notify_reqs=True)
        except RequirementFail:
            await self.bot.say("That module has requirements that I could not "
                               "install. Check the console for more "
                               "informations.")
            return
        if data is not None:
            install_msg = data.get("INSTALL_MSG", None)
            if install_msg:
                await self.bot.say(install_msg[:2000])
        if install_module:
            await self.bot.say("Installation completed. Load it now? (yes/no)")
            answer = await self.bot.wait_for_message(timeout=15,
                                                     author=ctx.message.author)
            if answer is None:
                await self.bot.say("Ok then, you can load it with"
                                   " `{}load {}`".format(ctx.prefix, module))
            elif answer.content.lower().strip() == "yes":
                set_module("modules." + module, True)
                owner = self.bot.get_module('Owner')
                await owner.load.callback(owner, module_name=module)
            else:
                await self.bot.say("Ok then, you can load it with"
                                   " `{}load {}`".format(ctx.prefix, module))
        elif install_module is False:
            await self.bot.say("Invalid module. Installation aborted.")
        else:
            await self.bot.say("That module doesn't exist. Use module list to see"
                               " the full list.")

    async def install(self, repo_name, module, *, notify_reqs=False,
                      no_install_on_reqs_fail=True):
        # 'no_install_on_reqs_fail' will make the module get installed anyway
        # on requirements installation fail. This is necessary because due to
        # how 'module update' works right now, the user would have no way to
        # reupdate the module if the update fails, since 'module update' only
        # updates the modules that get a new commit.
        # This is not a great way to deal with the problem and a module update
        # rework would probably be the best course of action.
        reqs_failed = False
        if module.endswith('.py'):
            module = module[:-3]

        path = self.repos[repo_name][module]['file']
        module_folder_path = self.repos[repo_name][module]['folder']
        module_data_path = os.path.join(module_folder_path, 'data')
        data = self.get_info_data(repo_name, module)
        if data is not None:
            requirements = data.get("REQUIREMENTS", [])

            requirements = [r for r in requirements
                            if not self.is_lib_installed(r)]

            if requirements and notify_reqs:
                await self.bot.say("Installing module's requirements...")

            for requirement in requirements:
                if not self.is_lib_installed(requirement):
                    success = await self.bot.pip_install(requirement)
                    if not success:
                        if no_install_on_reqs_fail:
                            raise RequirementFail()
                        else:
                            reqs_failed = True

        to_path = os.path.join("modules", module + ".py")

        print("Copying {}...".format(module))
        shutil.copy(path, to_path)

        if os.path.exists(module_data_path):
            print("Copying {}'s data folder...".format(module))
            distutils.dir_util.copy_tree(module_data_path,
                                         os.path.join('data', module))
        self.repos[repo_name][module]['INSTALLED'] = True
        self.save_repos()
        if not reqs_failed:
            return True
        else:
            raise RequirementFail()

    def get_info_data(self, repo_name, module=None):
        if module is not None:
            modules = self.list_modules(repo_name)
            if module in modules:
                info_file = os.path.join(modules[module].get('folder'), "info.json")
                if os.path.isfile(info_file):
                    try:
                        data = dataIO.load_json(info_file)
                    except:
                        return None
                    return data
        else:
            repo_info = os.path.join(self.path, repo_name, 'info.json')
            if os.path.isfile(repo_info):
                try:
                    data = dataIO.load_json(repo_info)
                    return data
                except:
                    return None
        return None

    def list_modules(self, repo_name):
        valid_modules = {}

        repo_path = os.path.join(self.path, repo_name)
        folders = [f for f in os.listdir(repo_path)
                   if os.path.isdir(os.path.join(repo_path, f))]
        legacy_path = os.path.join(repo_path, "modules")
        legacy_folders = []
        if os.path.exists(legacy_path):
            for f in os.listdir(legacy_path):
                if os.path.isdir(os.path.join(legacy_path, f)):
                    legacy_folders.append(os.path.join("modules", f))

        folders = folders + legacy_folders

        for f in folders:
            module_folder_path = os.path.join(self.path, repo_name, f)
            module_folder = os.path.basename(module_folder_path)
            for module in os.listdir(module_folder_path):
                module_path = os.path.join(module_folder_path, module)
                if os.path.isfile(module_path) and module_folder == module[:-3]:
                    valid_modules[module[:-3]] = {'folder': module_folder_path,
                                            'file': module_path}
        return valid_modules

    def get_dir_name(self, url):
        splitted = url.split("/")
        git_name = splitted[-1]
        return git_name[:-4]

    def is_lib_installed(self, name):
        return bool(find_spec(name))

    def _do_first_run(self):
        save = False
        repos_copy = deepcopy(self.repos)

        # Issue 725
        for repo in repos_copy:
            for module in repos_copy[repo]:
                module_data = repos_copy[repo][module]
                if isinstance(module_data, str):  # ... url field
                    continue
                for k, v in module_data.items():
                    if k in ("file", "folder"):
                        repos_copy[repo][module][k] = os.path.normpath(module_data[k])

        if self.repos != repos_copy:
            self.repos = repos_copy
            save = True

        invalid = []

        for repo in self.repos:
            broken = 'url' in self.repos[repo] and len(self.repos[repo]) == 1
            if broken:
                save = True
                try:
                    self.update_repo(repo)
                    self.populate_list(repo)
                except CloningError:
                    invalid.append(repo)
                    continue
                except Exception as e:
                    print(e) # TODO: Proper logging
                    continue

        for repo in invalid:
            del self.repos[repo]

        if save:
            self.save_repos()

    def populate_list(self, name):
        valid_modules = self.list_modules(name)
        new = set(valid_modules.keys())
        old = set(self.repos[name].keys())
        for module in new - old:
            self.repos[name][module] = valid_modules.get(module, {})
            self.repos[name][module]['INSTALLED'] = False
        for module in new & old:
            self.repos[name][module].update(valid_modules[module])
        for module in old - new:
            if module != 'url':
                del self.repos[name][module]

    def update_repo(self, name):

        def run(*args, **kwargs):
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            kwargs['env'] = env
            return sp_run(*args, **kwargs)

        try:
            dd = self.path
            if name not in self.repos:
                raise UpdateError("Repo does not exist in data, wtf")
            folder = os.path.join(dd, name)
            # Make sure we don't git reset the ProjectPython folder on accident
            if not os.path.exists(os.path.join(folder, '.git')):
                #if os.path.exists(folder):
                    #shutil.rmtree(folder)
                url = self.repos[name].get('url')
                if not url:
                    raise UpdateError("Need to clone but no URL set")
                branch = None
                if "@" in url: # Specific branch
                    url, branch = url.rsplit("@", maxsplit=1)
                if branch is None:
                    p = run(["git", "clone", url, folder])
                else:
                    p = run(["git", "clone", "-b", branch, url, folder])
                if p.returncode != 0:
                    raise CloningError()
                self.populate_list(name)
                return name, REPO_CLONE, None
            else:
                rpbcmd = ["git", "-C", folder, "rev-parse", "--abbrev-ref", "HEAD"]
                p = run(rpbcmd, stdout=PIPE)
                branch = p.stdout.decode().strip()

                rpcmd = ["git", "-C", folder, "rev-parse", branch]
                p = run(["git", "-C", folder, "reset", "--hard",
                        "origin/%s" % branch, "-q"])
                if p.returncode != 0:
                    raise UpdateError("Error resetting to origin/%s" % branch)
                p = run(rpcmd, stdout=PIPE)
                if p.returncode != 0:
                    raise UpdateError("Unable to determine old commit hash")
                oldhash = p.stdout.decode().strip()
                p = run(["git", "-C", folder, "pull", "-q", "--ff-only"])
                if p.returncode != 0:
                    raise UpdateError("Error pulling updates")
                p = run(rpcmd, stdout=PIPE)
                if p.returncode != 0:
                    raise UpdateError("Unable to determine new commit hash")
                newhash = p.stdout.decode().strip()
                if oldhash == newhash:
                    return name, REPO_SAME, None
                else:
                    self.populate_list(name)
                    self.save_repos()
                    ret = {}
                    cmd = ['git', '-C', folder, 'diff', '--no-commit-id',
                           '--name-status', oldhash, newhash]
                    p = run(cmd, stdout=PIPE)

                    if p.returncode != 0:
                        raise UpdateError("Error in git diff")

                    changed = p.stdout.strip().decode().split('\n')

                    for f in changed:
                        if not f.endswith('.py'):
                            continue

                        status, _, modulepath = f.partition('\t')
                        modulename = os.path.split(modulepath)[-1][:-3]  # strip .py
                        if status not in ret:
                            ret[status] = []
                        ret[status].append(modulename)

                    return name, ret, oldhash

        except CloningError as e:
            raise CloningError(name, *e.args) from None
        except UpdateError as e:
            raise UpdateError(name, *e.args) from None

    async def _robust_edit(self, msg, text):
        try:
            msg = await self.bot.edit_message(msg, text)
        except discord.errors.NotFound:
            msg = await self.bot.send_message(msg.channel, text)
        except:
            raise
        return msg

    @staticmethod
    def format_patch(repo, module, log):
        header = "Patch Notes for %s/%s" % (repo, module)
        line = "=" * len(header)
        if log:
            return '\n'.join((header, line, log))


def check_folders():
    if not os.path.exists(os.path.join("data", "downloader")):
        print('Making repo downloads folder...')
        os.mkdir(os.path.join("data", "downloader"))


def check_files():
    f = os.path.join("data", "downloader", "repos.json")
    if not dataIO.is_valid_json(f):
        print("Creating default data/downloader/repos.json")
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    n = Downloader(bot)
    bot.add_module(n)
