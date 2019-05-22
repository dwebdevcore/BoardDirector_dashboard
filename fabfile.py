# -*- coding: utf-8 -*-
from datetime import datetime
from glob import glob
from os import path, sep
from re import match, split
from StringIO import StringIO

from fabric.api import run, sudo, local, cd, put, task
from fabric.api import abort, warn
from fabric.api import hide, env, settings, prefix
from fabric.colors import green, yellow, red
from fabric.contrib.files import exists as path_exists


# Environment definitions
ENV_MAP = {
    'production': {
        'hosts': ['www.boarddirector.co'],
        'user': 'ubuntu',
        'project_name': 'boarddirector',
        'db_name': 'boarddocuments_db',
        # 'repo': 'git@git.steelkiwi.com:web/boarddocuments.git',     # old, until 30-Sep-2015
        'repo': 'git@bitbucket.org:boarddirector/boarddirector.git',  # new, from 30-Sep-2015
        'base_dir': '/home/ubuntu/www/app',
        'settings_local': 'settings/local.py.example',
    },
}


def env_value(env, value):
    """Returns value from env"""
    return ENV_MAP[env][value]


# Support classes
class Deployment(object):

    home_dir = "/home/ubuntu"
    base_deploy_dir = path.join(home_dir, "www")
    virtualenv_dir = path.join(base_deploy_dir, "env")
    conf_dir = path.join(base_deploy_dir, "conf")

    @classmethod
    def app_dir(cls, release=None):
        app_path = path.join(cls.base_deploy_dir, "app")
        if release is not None:
            app_path = path.join(app_path, "release", release)
        return app_path

    @classmethod
    def parse_release_from_path(cls, p):
        release_dir = cls.app_dir(release="")
        if p.startswith(release_dir):
            release_str = p[len(release_dir):].rstrip(sep)
            if release_str:
                return release_str
        return None

    @classmethod
    def update_virtualenv(cls, release=None):
        with settings(hide('running', 'stdout')):
            with cd(cls.app_dir(release)):
                with prefix("source %s/bin/activate" % cls.virtualenv_dir):
                    return run("pip install --exists-action=s -r requirements.txt")

    @classmethod
    def collectstatic(cls, release=None):
        with settings(hide('running', 'stdout')):
            with cd(cls.app_dir(release)):
                with prefix("source %s/bin/activate" % cls.virtualenv_dir):
                    return run("python manage.py collectstatic --noinput")

    @property
    def active_release(self):
        return uWSGI().active_release


class Service(object):
    _service_name = None            # name of the Linux service (specified in init.d)
    _process_name = None            # name of the server process (executable name)
    _conf_template = None           # path of the config file template (source path, relative to this directory)
    _conf_destination = None        # destination path of the config file on the server
    _post_config_commands = []      # room for extra shell commands, executed after the config file is deployed
    _good_status = "is running"     # string indicating that the service is running
    _bad_status = "not running"     # string indicating that the service is not running
    _conf_needs_sudo = False        # configuration file access and post-configuration steps: sudo or regular user?
    _run_needs_sudo = False         # service control: sudo or regular user?

    def __init__(self, conf_args=None):
        self._conf_args = conf_args or {}

    def __control_service(self, cmd):
        fab_func = self._run_needs_sudo and sudo or run
        with settings(hide('running', 'stdout'), warn_only=True):
            result = fab_func("service %s %s" % (self._service_name, cmd))
        if result.succeeded:
            cmd += cmd == "stop" and "ped" or "ed"
            print green("%s service %s" % (cmd, self._service_name))
        else:
            print red("Failed to %s service %s" % (cmd, self._service_name))
            warn(red("This needs your attention!"))

    def __log_check_result(self, service_running):
        status_msg = service_running and "running" or "not running"
        log_color = service_running and green or red
        print "Service %s: [%s]" % (self._service_name, log_color(status_msg))

    def __query_processes(self):
        remote_stdout = StringIO()
        pids = []
        with settings(hide('running'), warn_only=True):
            cmd = "ps -Aef | grep %s | grep -v grep | gawk '{print $2}'" % self.process_name
            result = run(cmd, stdout=remote_stdout)
            if result.failed:
                warn(yellow("Unable to query remaining %s processes!" % self._service_name))
                return []
        remote_stdout.seek(0)
        output = remote_stdout.readlines()
        for line in output:
            m = match("^.*?out\:\s+(?P<pids>[0-9\ \t]*)$", line.rstrip("\n"))
            pids_str = m and m.groupdict()["pids"].strip() or ""
            pids += map(int, filter(lambda s: s.isdigit(), pids_str.split()))
        return pids

    @property
    def template_path(self):
        return path.join(path.dirname(path.abspath(__file__)), self._conf_template)

    @property
    def process_name(self):
        return self._process_name or self._service_name

    def configure(self):
        # Prepare configuration file contents
        with open(self.template_path, "rb") as template:
            config = template.read() % self._conf_args

        # Deploy configuration file on server
        with settings(hide('running', 'stdout'), warn_only=True):
            result = put(
                local_path=StringIO(config),
                remote_path=self._conf_destination,
                use_sudo=self._conf_needs_sudo)
            if result.succeeded:
                print green("Configured service %s" % self._service_name)
            else:
                print red("Failed to configure service %s" % self._service_name)
                abort(red("Cannot continue"))

        # Execute extra post-config commands
        if self._post_config_commands:
            fab_func = self._conf_needs_sudo and sudo or run
            with settings(hide('running', 'stdout'), warn_only=True):
                for cmd in self._post_config_commands:
                    result = fab_func(cmd)
                    if result.failed:
                        break
            if result.succeeded:
                print green("Applied post-configuration for service %s" % self._service_name)
            else:
                warn(yellow("Unable to apply post-configuration for service %s" % self._service_name))

    def stop(self):
        self.__control_service("stop")

    def kill(self):
        pids = self.__query_processes()
        if pids:
            pid_str = " ".join([str(p) for p in pids])
            with settings(hide('running')):
                print yellow("Killing %s processes: %s ..." % (self._service_name, pid_str))
                sudo("kill -9 %s" % pid_str)

    def start(self):
        self.__control_service("start")

    def restart(self):
        self.__control_service("restart")

    def check(self):
        # Execute command to check the service status
        remote_stdout = StringIO()
        remote_stderr = StringIO()
        with settings(hide('running'), warn_only=True):
            result = run("service %s status" % self._service_name,
                         stdout=remote_stdout,
                         stderr=remote_stderr)
        if result.failed:
            warn(yellow("Unable to check status for service %s" % self._service_name))
            return False

        # Collect and evaluate the output
        remote_stdout.seek(0)
        remote_stderr.seek(0)
        output = "\n".join([remote_stdout.read(), remote_stderr.read()])
        if self._bad_status in output:
            service_running = False
        elif self._good_status in output:
            service_running = True
        else:
            service_running = False
        self.__log_check_result(service_running)
        return service_running


class Supervisor(Service):
    _service_name = "supervisor"
    _process_name = "supervisord"
    _conf_template = "conf/supervisord.conf"
    _conf_destination = "/etc/supervisor/conf.d/boarddirector.conf"
    _post_config_commands = [
       "chown root: %s" % _conf_destination,
       "chmod 644 %s" % _conf_destination]
    _conf_needs_sudo = True

    def stop(self):
        # Stop may sometimes fail, so we proceed with a kill
        super(self.__class__, self).stop()
        self.kill()

    def restart(self):
        # Use nondefault stop() method also in restart()
        self.stop()
        self.start()


class uWSGI(Service):
    """
    Service uWSGI running as foreground process under the supervisor daemon.
    """
    _service_name = "uwsgi"
    _conf_template = "conf/uwsgi.ini"
    _conf_destination = path.join(Deployment.conf_dir, path.basename(_conf_template))

    def __supervisorctl(self, cmd):
        remote_stdout = StringIO()
        remote_stderr = StringIO()
        with settings(hide('running'), warn_only=True):
            result = run("/usr/bin/supervisorctl %s %s" % (cmd, self._service_name),
                         stdout=remote_stdout,
                         stderr=remote_stderr)
        remote_stdout.seek(0)
        remote_stderr.seek(0)
        output = "\n".join([remote_stdout.read(), remote_stderr.read()])

        expected_str = "uwsgi: "
        if cmd == "stop":
            expected_str += "stopped"
        else:
            expected_str += "started"
        if "ERROR" in output:
            warn(yellow("supervisorctl reported error:"))
            print output
            return False
        elif expected_str in output:
            return True
        else:
            return False

    def configure(self, release=None):
        self._conf_args["appdir"] = Deployment.app_dir(release)
        super(self.__class__, self).configure()

    def stop(self):
        stopped = self.__supervisorctl("stop")
        if stopped:
            print green("Stopped service %s" % self._service_name)
        else:
            print "Retry with kill..."
            self.kill()
            self.__supervisorctl("stop")

    def start(self):
        started = self.__supervisorctl("start")
        if started:
            print green("Started service %s" % self._service_name)
        else:
            print red("Unable to start service %s" % self._service_name)
            abort(red("Cannot continue"))

    def restart(self):
        restarted = self.__supervisorctl("restart")
        if restarted:
            print green("Restarted service %s" % self._service_name)
        else:
            print "Failed to restart. Attempting kill/restart cycle..."
            self.kill()
            restarted = self.__supervisorctl("restart")
            if restarted:
                print green("Restarted service %s" % self._service_name)
            else:
                print red("Unable to restart service %s" % self._service_name)
                abort(red("Cannot continue"))

    @property
    def active_release(self):
        remote_stdout = StringIO()
        with settings(hide('running'), warn_only=True):
            cmd = "grep chdir %s | gawk '{print $(NF)}'" % self._conf_destination
            result = run(cmd, stdout=remote_stdout)
            if result.failed:
                warn(yellow("Unable to query the release from uWSGI config!"))
                return None
        remote_stdout.seek(0)
        output = remote_stdout.readlines()
        for line in output:
            m = match("^.*?out\:\s+(?P<path>\S+)$", line.rstrip("\n"))
            if m:
                release = Deployment.parse_release_from_path(m.groupdict()["path"])
                if release:
                    return release
        return None


class Nginx(Service):
    _service_name = "nginx"
    _conf_template = "conf/nginx/boarddirector.conf"
    _conf_destination = "/etc/nginx/sites-available/boarddirector"
    _post_config_commands = [
        "chown root: %s" % _conf_destination,
        "chmod 644 %s" % _conf_destination,
        "ln -s %s /etc/nginx/sites-enabled/" % _conf_destination]
    _conf_needs_sudo = True
    _run_needs_sudo = True


class Repository(object):
    _provider = "bitbucket.org"
    _account = "boarddirector"
    _project = "boarddirector"
    _download_format = "tar.gz"

    def __init__(self):
        self._download_folder = "/tmp"

    @property
    def source(self):
        return {"provider": self._provider,
                "account": self._account,
                "project": self._project}

    @property
    def download_folder(self):
        return self._download_folder

    @download_folder.setter
    def set_download_folder(self, value):
        self._download_folder = value

    @property
    def git_url(self):
        return "git@%(provider)s:%(account)s/%(project)s.git" % self.source

    def __output_path(self, release):
        filename = "%s-%s.%s" % (self._project, release, self._download_format)
        return path.join(self.download_folder, filename)

    def download_release(self, release):
        local_path = self.__output_path(release)
        print "Downloading release %s to local file %s" % (release, local_path)
        local_path = self.__output_path(release)
        cmd = "git archive --remote=%s --format=%s --output=/%s %s" % \
              (self.git_url, self._download_format, local_path, release)
        with settings(hide('running', 'stdout'), warn_only=True):
            result = local(cmd)
        if result.succeeded:
            print green("Download successful")
            return local_path
        else:
            print red("Download failed!")
            abort(red("Cannot continue"))


class Migrations(object):
    def __init__(self, release):
        self._release = release
        self._path = Deployment.app_dir(release)
        self._migrations = self.__scan()

    @staticmethod
    def __migration_nr(filename):
        s = split("\_+", filename)[0]
        if s.isdigit():
            return int(s)
        else:
            return None

    @staticmethod
    def __parse_line(line):
        parts = line.split(sep)
        return (parts[1], parts[3])

    @classmethod
    def __to_dict(cls, lines):
        d = {}
        for line in lines:
            (app, filename) = cls.__parse_line(line)
            if filename != "__init__.py":
                if app not in d:
                    d[app] = set()
                d[app].add(filename)
        return d

    def __scan(self):
        if not path_exists(self._path):
            raise OSError("No deployment of release %s found!" % self._release)
        with cd(self._path):
            with settings(hide('running', 'stdout')):
                ptrn = path.join("apps", "*", "migrations", "*.py")
                output = run("ls -1 %s" % ptrn)
        return self.__to_dict(output.splitlines())

    def __compare_app(self, other, app):
        m1 = self.migrations.get(app, set())
        m2 = other.migrations.get(app, set())
        return {"left": m1-m2,
                "common": m1 & m2,
                "right": m2-m1}

    def __manage_cmd(self, cmd):
        with cd(self._path):
            with prefix("source %s/bin/activate" % Deployment.virtualenv_dir):
                return run("python manage.py %s" % cmd)

    @property
    def migrations(self):
        return self._migrations

    def compare(self, other):
        """
        Compares the migrations in this deployment with those in the other deployment.
        :param other: migrations in other deployment
        :return: for each app, three sets:
                 - left: only present in this deployment
                 - right: only present in the other deployment
                 - common: present in both deployments
        """
        all_apps = set(self.migrations.keys()) | set(other.migrations.keys())
        return {app: self.__compare_app(other, app) for app in all_apps}

    def revert_left(self, other):
        """
        Reverts all migrations which are present in this deployment but not in the other.
        """
        delta = self.compare(other)
        failures = dict()
        for app in delta:
            to_revert = delta[app]["left"]  # filenames
            if to_revert:
                common_migrations = delta[app]["common"]
                if common_migrations:
                    latest_common_migration = max([self.__migration_nr(fn) for fn in common_migrations])
                else:
                    latest_common_migration = None

                if latest_common_migration is not None:
                    revert_to_nr = "%04d" % latest_common_migration
                else:
                    revert_to_nr = "zero"

                revert_str = " ".join(["%04d" % n for n in sorted([self.__migration_nr(fn) for fn in to_revert])])
                print "Reverting migrations for app %s: %s ..." % (app, revert_str)
                with settings(hide('running', 'stdout'), warn_only=True):
                    result = self.__manage_cmd("migrate %s %s" % (app, revert_to_nr))
                    if result.failed:
                        failures[app] = "(stdout): %s\n(stderr): %s" % (result.stdout, result.stderr)
        for app in failures:
            warn(red("Failed to revert superfluous migrations for app %s" % app))
            print "Details:\n%s" % failures[app]
        if failures:
            warn(red("This needs your attention!"))

    def apply(self):
        print "Applying database changes for release %s ..." % self._release
        with settings(hide('running', 'stdout')):
            self.__manage_cmd("syncdb")
            self.__manage_cmd("migrate")
            self.__manage_cmd("loaddata flatpages")
        print "done"


# Tasks
env.hosts = env_value('production', 'hosts')
env.user = env_value('production', 'user')
env.base_dir = env_value('production', 'base_dir')
env.local_settings = env_value('production', 'settings_local')
env.project_name = Deployment.app_dir(),
env.db_name = env_value('production', 'db_name')
env.project_dir = env.base_dir


@task
def restart_uwsgi():
    """
    Restarts the uWSGI application server
    """
    uwsgi = uWSGI()
    uwsgi.restart()


@task
def activate(release=None):
    """
    fab activate:<tag> -- Configures and restarts the services to run the specified release
    :param release: GIT branch or tag name; skip to activate the legacy deployment
    """
    def release_str(release):
        if release is not None:
            return str(release)
        else:
            return "(legacy)"
    print "Activate release: %s" % release_str(release)

    # Check if the new release has been deployed
    deploy = Deployment()
    deploy_path = deploy.app_dir(release)
    if not path_exists(deploy_path):
        print red("Cannot activate release: no matching deployment found!")
        abort(red("Cannot continue"))
    env.project_dir = deploy_path

    # Stop services before touching the database
    downtime_start = datetime.utcnow()
    nginx = Nginx()
    uwsgi = uWSGI()
    nginx.stop()
    uwsgi.stop()

    # Update the pip packages
    deploy.update_virtualenv(release)

    # Rollback superfluous migrations from the current release
    current_migrations = Migrations(deploy.active_release)
    new_migrations = Migrations(release)
    current_migrations.revert_left(new_migrations)

    # Apply database changes for the new release
    new_migrations.apply()

    # Configure and start the services
    uwsgi.configure(release)
    uwsgi.start()
    nginx.start()
    downtime_end = datetime.utcnow()

    print green("Activated release %s" % release_str(uwsgi.active_release))
    print "Downtime: %s" % (downtime_end - downtime_start)


@task
def deploy(release):
    """
    fab deploy:<tag> -- Installs the specified release on the server
    :param release: GIT branch or tag name
    """
    print "Deploying release: %s" % release

    # Download file from git repository
    repo = Repository()
    local_path = repo.download_release(release)

    # Deploy to server
    deploy_path = Deployment.app_dir(release)
    env.project_dir = deploy_path
    to_deploy = ["apps", "settings", "flatpages.json", "manage.py", "requirements.txt", "wsgi.py"]
    files_to_retain = set([".", ".."] + to_deploy)

    if path_exists(deploy_path):
        print red("Cannot deploy release: folder already exists!")
        abort(red("Cannot continue"))
    try:
        with settings(hide('running', 'stdout')):
            run("mkdir -p %s" % deploy_path)
            put(local_path=local_path,
                remote_path=deploy_path,
                mode=0644)
            with cd(deploy_path):
                run("tar xvf %s" % path.basename(local_path))
                files = set(run("ls -a").split())
                files_to_remove = files - files_to_retain
                print "cleaning up..."
                run("rm -rf %s" % " ".join(files_to_remove))
                print "done"

            # Patch settings files
            settings_ptrn = path.join(path.dirname(path.abspath(__file__)), "settings", "production", "*.py")
            for fn in glob(settings_ptrn):
                put(local_path=fn, remote_path=path.join(deploy_path, "settings"), mode=0644)

            # Collect static files
            print "Collecting static files..."
            Deployment.collectstatic(release)

        print green("Successfully deployed release %s" % release)
    except Exception, e:
        print red("Deployment encountered error: %s" % e)
        abort(red("Cannot continue"))


@task
def remove(release):
    """
    fab remove:<tag> -- Removes the specified release from the server
    :param release: GIT branch or tag name
    """
    print "Removing release: %s" % release
    depl = Deployment()
    try:
        if not release:
            raise ValueError("Cannot remove release from legacy path (only side by side installations may be deleted)")
        elif release == depl.active_release:
            raise ValueError("Cannot remove active release")
        elif not path_exists(Deployment.app_dir(release)):
            raise OSError("Cannot remove release: no deployment found!")
        else:
            with settings(hide('running', 'stdout'), warn_only=True):
                result = run("rm -rf %s" % Deployment.app_dir(release))
                if result.succeeded:
                    print green("Successfully removed deployment of release %s" % release)
                else:
                    raise OSError("Failed to delete deployment folder!")
    except (OSError, ValueError), e:
        print red(e.message)
        abort(red("Cannot continue"))
