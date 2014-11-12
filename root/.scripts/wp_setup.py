#! /usr/bin/env python

import os, sys, json, re, shutil
import subprocess
import shlex
import argparse
import urlparse
import urllib2
from git import *

## Just in case we want change env prefix or remove it latter, default all envs start with prefix FACTER_ , example : FACTER_W3D_WWW_ROOT
env_prefix = 'FACTER_'
tmp_repo_folder = '/media/tmp_w3tc_repo/'

class MyArgparse(argparse.ArgumentParser):
    """Override error handling for argparser to allow us print help if no params or any error occurred"""
    def error(self, message):
        sys.stderr.write('Error: %s\n' % message)
        self.print_help()
        sys.exit(2)

### Fetch variables from Evriorment to st as default Values to options if exists, otherwise set None to force manual parameters to be placed.
def get_db_name():
    if env_prefix + 'W3D_WP_DB_NAME' in os.environ:
        return os.environ[env_prefix+'W3D_WP_DB_NAME']
    else:
        return None

def get_db_user():
    if env_prefix + 'W3D_WP_DB_USER' in os.environ:
        return os.environ[env_prefix+'W3D_WP_DB_USER']
    else:
        return None

def get_db_pass():
    if env_prefix + 'W3D_WP_DB_PASS' in os.environ:
        return os.environ[env_prefix+'W3D_WP_DB_PASS']
    else:
        return None

def get_db_src(src_type=''):
    if env_prefix + 'W3D_DB_SRC' in os.environ:
        parts = urlparse.urlparse(os.environ[env_prefix + 'W3D_DB_SRC'])
        if parts.scheme not in ['http', 'https'] and src_type == 'file':
            return os.environ[env_prefix + 'W3D_DB_SRC']
        elif parts.scheme in ['http', 'https'] and src_type == 'http':
            return os.environ[env_prefix + 'W3D_DB_SRC']
    else:
        return None

def get_www_root():
    if env_prefix + 'W3D_WWW_ROOT' in os.environ:
        return os.environ[env_prefix+'W3D_WWW_ROOT']
    else:
        return "/www/"

def get_old_domain():
    args = shlex.split("/usr/bin/wp --allow-root --path="+get_www_root()+" db query \"select option_value from wp_options WHERE option_name = 'siteurl';\"")
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    if not err:
        pre = re.compile("(https?://)([^:^/]*)(:\\d*)?(.*)?")
        return pre.match(output.split("\n")[1]).groups()[1]
    else:
        return None

def get_new_domain():
    if env_prefix + 'W3D_DOMAIN' in os.environ:
        return os.environ[env_prefix+'W3D_DOMAIN']
    else:
        return None

def get_wp_version():
    if env_prefix + 'W3D_WP_VERSION' in os.environ:
        return os.environ[env_prefix+'W3D_WP_VERSION']
    else:
        return None

def get_env_repo():
    if env_prefix + 'W3D_W3TC_REPO' in os.environ:
        return os.environ[env_prefix+'W3D_W3TC_REPO']
    else:
        return None

def get_env_branch():
    if env_prefix + 'W3D_W3TC_BRANCH' in os.environ:
        return os.environ[env_prefix+'W3D_W3TC_BRANCH']
    else:
        return 'master'

def get_env_commit():
    if env_prefix + 'W3D_W3TC_COMMIT' in os.environ:
        return os.environ[env_prefix+'W3D_W3TC_COMMIT']
    else:
        return None

def get_env_active_plugins():
    if env_prefix + 'W3D_ACTIVE_PLUGINS' in os.environ:
        return os.environ[env_prefix+'W3D_ACTIVE_PLUGINS']
    else:
        return None

def get_env_inactive_plugins():
    if env_prefix + 'W3D_INACTIVE_PLUGINS' in os.environ:
        return os.environ[env_prefix+'W3D_INACTIVE_PLUGINS']
    else:
        return None


## Option menu definition
def options():
    """Parameters definition"""
    args = MyArgparse()
    # args.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    
    args.prog = "wp_setup.py"
    args.description = "Wordpress Setup utility, wrapper for WP-CLI commands for Install WP and Setup DB and Git Clone command."
    args.usage = "%(prog)s [options]"
    args.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    subparsers = args.add_subparsers(help='command help')
    # Defaine 'db' actions
    args_db = subparsers.add_parser('db', help='Wordpress Database Setup. For more help use: db help')
    args_db.description = "Wordpress DB Setup. Default values taked from ENV variables if exists,\n otherwise should be added as parameters."
    args_db.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    # DB Subcommands
    db_subparsers = args_db.add_subparsers(help='command help')
    # Db -> Inmport
    args_db_import = db_subparsers.add_parser('import', help='Import Wordpress database.')
    args_db_import.set_defaults(func=db_import)
    args_db_import.add_argument('--path', help='Specify the path in which to install WordPress.', required=False, default=get_www_root())
    db_import_group = args_db_import.add_mutually_exclusive_group(required=False)
    args_db_import.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_db_import.description = "Only one option allowed in a time, File or URL."
    db_import_group.add_argument('--file', help='Set SQL db dump file as full path location.', default=get_db_src(src_type='file'))
    db_import_group.add_argument('--url', help='Set SQL db dump file as full URL location.', default=get_db_src(src_type='http'))
    # DB -> Replace
    args_db_replace = db_subparsers.add_parser('replace', help='Search/replace strings in the database.')
    args_db_replace.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_db_replace.set_defaults(func=db_replace)
    args_db_replace.add_argument('--path', help='Specify the path in which to install WordPress.', required=False, default=get_www_root())
    args_db_replace.add_argument('--src', help='Source string to search', required=False, default=get_old_domain())
    args_db_replace.add_argument('--dst', help='Destination string to replace', required=False, default=get_new_domain())

    # Define core actions
    args_core = subparsers.add_parser('core', help='Wordpress Core installation. For more help use: core help')
    args_core.description = "Wordpress CORE Setup. Default values taked from ENV variables if exists,\n otherwise should be added as parameters."
    args_core.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    # Core Subcommands
    core_subparsers = args_core.add_subparsers(help='command help')
    # Core -> Config
    args_core_config = core_subparsers.add_parser('config', help='Wordpress Config file configuration')
    args_core_config.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_core_config.add_argument('--path', help='Specify the path in which to install WordPress.', required=False, default=get_www_root())
    args_core_config.add_argument('--dbname', help='Set the database name.', required=False, default=get_db_name())
    args_core_config.add_argument('--dbuser', help='Set the database user.', default=get_db_user())
    args_core_config.add_argument('--dbpass', help='Set the database user password.', default=get_db_pass())
    args_core_config.add_argument('--dbhost', help='Set the database host.', default='localhost')
    args_core_config.add_argument('--dbprefix', help='Set the database table prefix.')
    args_core_config.add_argument('--dbcharset', help='Set the database charset.')
    args_core_config.add_argument('--dbcollate', help='Set the database collation.')
    args_core_config.add_argument('--locale', help='Set the WPLANG constant. Defaults to $wp_local_package variable.')
    args_core_config.add_argument('--extra-php', help='If set, the command copies additional PHP code into wp-config.php from STDIN.')
    args_core_config.add_argument('--skip-salts', help='If set, keys and salts wont be generated, but should instead be passed via `--extra-php`.', action='store_true')
    args_core_config.add_argument('--skip-check', help='If set, the database connection is not checked.', action='store_true')
    args_core_config.set_defaults(func=core_config)
    # Core -> Downloads
    args_core_download = core_subparsers.add_parser('download', help='Wordpress Download and unpack into target directory')
    args_core_download.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_core_download.add_argument('--path', help='Specify the path in which to install WordPress.', required=False, default=get_www_root())
    args_core_download.add_argument('--locale', help='Select which language you want to download.')
    args_core_download.add_argument('--version', help='Select which version you want to download.', required=False, default=get_wp_version())
    args_core_download.add_argument('--force', help='Overwrites existing files, if present.', action='store_true')
    args_core_download.set_defaults(func=core_download)

    # Git Related commdns
    args_git = subparsers.add_parser('git', help='Git Wrapper for clone , checkout and copy files. For more help use: core help')
    args_git.description = "Git Wrapper. Default values taked from ENV variables if exists,\n otherwise should be added as parameters."
    args_git.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    # Git Subcommands
    git_subparsers = args_git.add_subparsers(help='command help')
    # Git -> Clone
    args_git_clone = git_subparsers.add_parser('clone', help='Wordpress Config file configuration')
    args_git_clone.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_git_clone.set_defaults(func=git_clone)
    args_git_clone.add_argument('--path', help='Specify the path of Wordpress instalation.', required=False, default=get_www_root())
    args_git_clone.add_argument('--repo', help='Specify the GitHub repo.', required=False, default=get_env_repo())
    args_git_clone.add_argument('--branch', help='Specify the brunch to clone.', required=False, default=get_env_branch())
    args_git_clone.add_argument('--commit', help='Specify the commit to clone.', required=False, default=get_env_commit())

    # Plugins Related commdns
    args_plugin = subparsers.add_parser('plugin', help='Wordpress plugin actions. For more help use: core help')
    args_plugin.description = "WP Plugin manipulation wrapper. Default values taked from ENV variables if exists,\n otherwise should be added as parameters."
    args_plugin.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    # Plugin Subcommands
    plugin_subparsers = args_plugin.add_subparsers(help='command help')
    # Plugin -> Activate
    args_plugin_activate = plugin_subparsers.add_parser('activate', help='Wordpress Plugin activation')
    args_plugin_activate.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_plugin_activate.set_defaults(func=plugin_activate)
    args_plugin_activate.add_argument('--path', help='Specify the path of Wordpress instalation.', required=False, default=get_www_root())
    args_plugin_activate.add_argument('--name', help='Plugin name to activate', required=False, default=get_env_active_plugins())

    # Plugin -> Deactivate
    args_plugin_deactivate = plugin_subparsers.add_parser('deactivate', help='Wordpress Plugin deactivation')
    args_plugin_deactivate.formatter_class = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    args_plugin_deactivate.set_defaults(func=plugin_deactivate)
    args_plugin_deactivate.add_argument('--path', help='Specify the path of Wordpress instalation.', required=False, default=get_www_root())
    args_plugin_deactivate.add_argument('--name', help='Plugin name to deactivate', required=False, default=get_env_inactive_plugins())

    ret = args.parse_args()
    return ret


#### Actions
def plugin_activate(args):
    print args

def plugin_deactivate(args):
    print args

def git_clone(args):
    # print args
    # check if repo already esists
    if os.path.exists(tmp_repo_folder):
        repo = Repo(tmp_repo_folder)
        # Back to master and pull changes
        repo.git.checkout(args.branch)
        repo.git.pull()
        # Switch to commit if it was set by Env variables or cli parameter
        if args.commit:
            repo.git.checkout(args.commit)
    else:
        # clone repo
        repo = Repo.clone_from(args.repo, tmp_repo_folder)
        # checkout to branch which is Env variables or passed thru cli parameter if both None - Default master or exit
        if args.branch:
            repo.git.checkout(args.branch)
            repo.git.pull()
        # If commit parameter in Env or passed thu cli parameter - checkout to commit
        if args.commit:
            repo.git.checkout(args.commit)

    if os.path.exists(args.path+'/wp-content/plugins/w3-total-cache/'):
        shutil.rmtree(args.path+'/wp-content/plugins/w3-total-cache/')
    repo.git.checkout_index(a=True, f=True, prefix=args.path+'/wp-content/plugins/w3-total-cache/')

    return 255

def db_import(args):
    # print args
    # returns 0 - good, >= 1  - error
    cmdopt = ['/usr/bin/wp', '--allow-root', '--path='+args.path, 'db', 'import', '-']
    # print cmdopt
    p = subprocess.Popen(cmdopt, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    tmpargs = vars(args)
    opts = ['path', 'file', 'url']
    for key in opts:
        if key in tmpargs and tmpargs[key] is not False and tmpargs[key] is not None:
            if key == 'url':
                for line in urllib2.urlopen(tmpargs[key]):
                    #print line
                    p.stdin.write(line)
    output, err = p.communicate()
#     if not err:
#         print output
#     else:
#         print err
#     print p.returncode
    return p.returncode


def db_replace(args):
    # returns 0 - good, >= 1  - error
    cmdopt = ['/usr/bin/wp', '--allow-root', 'search-replace']
    tmpargs = vars(args)
    opts = ['path', 'src', 'dst']
    for key in opts:
        if key in tmpargs and tmpargs[key] is not False and tmpargs[key] is not None:
            if tmpargs[key] is True:
                cmdopt.extend(["--" + key])
            elif key == 'src' or key == 'dst':
                cmdopt.extend([tmpargs[key]])
            else:
                cmdopt.extend(["--" + key+'='+tmpargs[key]])
    p = subprocess.Popen(cmdopt, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
#    if not err:
#        print output
#    else:
#        print err
#    print p.returncode
    return p.returncode

def core_config(args):
    # print args
    # returns 0 - good, >= 1  - error
    # Remove previouse wp-config.php file from current WWW Root if exists before start configuration otherwise wp-cli return file exists.
    try:
        os.remove(args.path+'/wp-config.php')
    except OSError:
        pass

    cmdopt = ['/usr/bin/wp', '--allow-root', 'core', 'config']
    tmpargs = vars(args)
    opts = ['path', 'dbname', 'dbuser', 'dbpass', 'dbhost', 'dbprefix', 'dbcharset', 'dbcollate', 'locale', 'skip-salts', 'skip-check', 'extra-php']
    for key in opts:
        if key in tmpargs and tmpargs[key] is not False and tmpargs[key] is not None:
            if tmpargs[key] is True:
                cmdopt.extend(["--" + key])
            else:
                cmdopt.extend(["--" + key+'='+tmpargs[key]])
    p = subprocess.Popen(cmdopt, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
#    if not err:
#        print output
#    else:
#        print err
#    print p.returncode
    return p.returncode



def core_download(args):
    # returns 0 - good, >= 1  - error
    # Create nested folder for WWW root
    if not os.path.exists(args.path):
        os.makedirs(args.path)
    cmdopt = ['/usr/bin/wp', '--allow-root', 'core', 'download']
    tmpargs = vars(args)
    opts = ['path', 'version', 'locale', 'force']
    for key in opts:
        if key in tmpargs and tmpargs[key] is not False and tmpargs[key] is not None:
            if tmpargs[key] is True:
                cmdopt.extend(["--" + key])
            else:
                cmdopt.extend(["--" + key+'='+tmpargs[key]])
    p = subprocess.Popen(cmdopt, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
#    if not err:
#        print output
#    else:
#        print err
#    print p.returncode
    return p.returncode

## Main loop
def main():
    """main function"""
    opts = options()
    errcode = opts.func(opts)
    raise SystemExit(errcode)

## Application start
if __name__ == '__main__':
    main()
