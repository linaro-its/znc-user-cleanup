# Introduction

When someone uses [ZNC](https://wiki.znc.in/ZNC), a directory is created for them under `config/users`.

When that user's account is deleted from ZNC, the corresponding directory is **not** deleted.

This repo provides two solutions:

1. A script which, when run, will find the directories belonging to users without accounts on ZNC and either move them to a nominated "trash" folder or delete them, depending on the configuration settings.

2. A ZNC module which, when loaded, will be triggered when a user account is deleted on ZNC and either move that user's directory to the nominated "trash" folder or delete it, depending on whether the folder path is specified or not.

# Using the script

Since the script has to move or delete folders on the ZNC server itself, this script has to be run on that server.

`pipenv` is used to create a Python virtual environment and install the required packages:

```
pipenv install
```

Take a copy of `sample_config.jsonc`, call it `config.jsonc` and adjust the parameters as explained in the comments in the configuration file.

The most important configuration parameter to review is `trashpath`. This is set to a dummy value in the sample file that, if left like this, will generate an error. The value must either be "" (in which case the script will delete any folders belonging to users without active ZNC accounts) or the path to a directory where the script will move the user directories.

To run the script:

```
cd <installation directory>
pipenv run python cleanup.py
```

**NOTE** It is entirely possible that it will be necessary to run this script with root credentials unless additional steps are taken to grant the required permissions on both the source and (optionally) destination directories to allow the user account being used to make the appropriate changes.

# Using the module

**WARNING! This code is very much a work-in-progress and should not be used on a production system.**

Since the module is written in Python, the ZNC module `modpython` needs to be enabled:

```
/znc loadmod modpython
```

This can also be done via the global settings on webadmin. Once enabled, you should see `deluserdir` as an available module and that can then be loaded:

```
/znc loadmod deluserdir trashdir=
/znc loadmod deluserdir trashdir=<path to trash directory>
```

Specifying `trashdir=` means that, when a user account is deleted, the corresponding user directory will be deleted as well.

Again, this can also be done via webadmin.
