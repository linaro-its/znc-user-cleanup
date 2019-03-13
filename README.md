# Introduction

When someone uses [ZNC](https://wiki.znc.in/ZNC), a directory is created for them under `config/users`.

When that user's account is deleted from ZNC, the corresponding directory is **not** deleted.

Whether or not that directory *should* be deleted is the topic of quite an old issue on [GitHub](https://github.com/znc/znc/issues/260).

The purpose of this repo is to provide a simple script which, when run, will find the directories belonging to users without accounts on ZNC and either move them to a nominated "trash" folder or delete them, depending on the configuration settings.

# Using the script

Since the script has to move or delete folders on the ZNC server itself, this script has to be run on that server.

`pipenv` is used to create a Python virtual environment and install the required packages:

```
pipenv install
```

Take a copy of `sample_config.jsonc`, call it `config.jsonc` and adjust the parameters as explained in the comments in the configuration file.

The most important configuration parameter to review is `trashpath`. This is blank in the sample file. If left like this, the script will delete any folders belonging to users without active ZNC accounts. If, instead, you want the directories moved elsewhere, you must set this to the appropriate path.

To run the script:

```
cd <installation directory>
pipenv run cleanup.py
```
