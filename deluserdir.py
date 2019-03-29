# This module extends ZNC so that, when a user account is deleted, the
# corresponding user directory is either deleted or moved to a designated
# trash directory.
#
# Copyright 2019 Philip Colmer, Linaro Ltd

import znc
import os
import shutil


# Derive from Module and Timer so that the RunJob function (which
# is needed for the Timer code) can access the nv values which
# are set up for the Module code to work.
class deluserdir(znc.Module, znc.Timer):
    description = (
        "Deletes or moves user directories to trash when a user account "
        "is deleted"
    )
    module_types = [znc.CModInfo.GlobalModule]
    has_args = True

    trashdir_setting = None

    def OnLoad(self, args, message):
        success = True
        # Check the args and store associated values
        arglist = args.split()
        for arg in arglist:
            k, v = arg.split("=")
            if k == "trashdir":
                self.trashdir_setting = v
            else:
                message.s = (
                    "'%s' is not recognised" % k
                )
                success = False
        if self.trashdir_setting is None:
            message.s = (
                "'trashdir' must be set either to an empty string or"
                " to the desired trash directory"
            )
            success = False
        # If trashdir is specified ...
        if success and self.trashdir_setting != "":
            # make sure it exists
            if not os.path.isdir(self.trashdir_setting):
                message.s = (
                    "The specified trash directory ('%s') cannot be found" %
                    self.trashdir_setting
                )
                success = False
            else:
                # make sure that we can write to it.
                success = os.access(
                    self.trashdir_setting,
                    os.R_OK | os.W_OK | os.X_OK
                )
                if not success:
                    message.s = (
                        "The specified trash directory ('%s') doesn't have the"
                        " correct access rights for the account running ZNC" %
                        self.trashdir_setting
                    )

        if success:
            if self.trashdir_setting == "":
                znc.CZNC.Get().Broadcast(
                    "deluserdir is loaded. User directories will be deleted"
                )
            else:
                znc.CZNC.Get().Broadcast(
                    "deluserdir is loaded. User directories will be moved"
                    " to '%s' when user accounts are deleted" %
                    self.trashdir_setting
                )
        return success

    def __output_table(self, t):
        i = 0
        s = znc.String()
        while t.GetLine(i, s):
            self.PutModule(s.s)
            i += 1

    def __output_users(self):
        try:
            dirs = next(os.walk(self.trashdir_setting))[1]
            # Create a table with all of the user directories list
            t = znc.CTable()
            t.AddColumn("Users in trash directory")
            for dir in dirs:
                t.AddRow()
                t.SetCell("Users in trash directory", dir)
            self.__output_table(t)
        except Exception as e:
            self.PutModule(
                "__output_users failed with %s" % str(e))

    def __output_status(self):
        if self.trashdir_setting == "":
            self.PutModule(
                "deluserdir is configured to delete user directories")
        else:
            self.PutModule(
                "deluserdir is configured to move user directories to "
                "'%s' when user accounts are deleted" % self.trashdir_setting)
        self.PutModule("To change this, unload and reload the module with the")
        self.PutModule("desired setting.")

    def __list_trash(self):
        if self.trashdir_setting == "":
            self.PutModule(
                "deluserdir is configured to delete user directories")
        else:
            self.__output_users()

    def __empty_trash(self):
        self.PutModule("Currently not implemented")

    def __emit_help(self):
        t = znc.CTable()
        t.AddColumn("Command")
        t.AddColumn("Description")
        t.AddRow()
        t.SetCell("Command", "status")
        t.SetCell(
            "Description",
            "Confirms the configuration of the deluserdir module")
        t.AddRow()
        t.SetCell("Command", "listtrash")
        t.SetCell(
            "Description",
            "Lists any directories in the configured trash directory")
        t.AddRow()
        t.SetCell("Command", "emptytrash")
        t.SetCell(
            "Description",
            "Deletes any directories in the configured trash directory")
        self.__output_table(t)

    def OnModCommand(self, message):
        try:
            if message == "status":
                self.__output_status()
            elif message == "listtrash":
                self.__list_trash()
            elif message == "emptytrash":
                self.__empty_trash()
            else:
                self.__emit_help()
        except Exception as e:
            self.PutModule(
                "deluserdir:OnModCommand failed with %s" % str(e))

    def OnDeleteUser(self, user):
        # This handler gets called before *anything* else happens to process
        # the user's deletion. As a result, we have to wait a bit to give ZNC
        # time to finish processing the deletion, otherwise that extra
        # processing can end up creating a "new" user directory.
        #
        # So let's set a timer and give ourselves a callback with the details
        # of the user being deleted.
        timer = self.CreateTimer(
            deluserdir,
            interval=4,
            cycles=1,
            description="Delete %s after 4 seconds" % user.GetCleanUserName()
        )
        timer.msg = user.GetUserPath()
        timer.trashdir_setting = self.trashdir_setting
        return znc.CONTINUE

    def __get_dstuserdir(self, userdir, trashdir):
        # We need to check that a directory doesn't already exist with the
        # user's name in the trash directory. If it does, we need to append
        # an incrementing digit until we don't have a clash.
        suffix = 1
        user = os.path.basename(userdir)
        test_path = os.path.join(trashdir, user)
        while os.path.isdir(test_path):
            new_user = "%s%s" % (user, suffix)
            suffix += 1
            test_path = os.path.join(trashdir, new_user)
        return test_path

    def __move_userdir(self, userdir, trashdir):
        dst_name = self.__get_dstuserdir(userdir, trashdir)
        shutil.move(userdir, dst_name)

    def RunJob(self):
        try:
            userdir = self.msg
            trashdir = self.trashdir_setting
            if trashdir == "":
                znc.CZNC.Get().Broadcast("Deleting %s" % userdir)
                shutil.rmtree(userdir)
            else:
                znc.CZNC.Get().Broadcast(
                    "Moving %s to trash dir" % userdir)
                self.__move_userdir(userdir, trashdir)
        except Exception as e:
            znc.CZNC.Get().Broadcast(
                "deluserdir:OnDeleteUser failed with %s" % str(e))
