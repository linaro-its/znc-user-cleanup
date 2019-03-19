# This module extends ZNC so that, when a user account is deleted, the
# corresponding user directory is either deleted or moved to a designated
# trash directory.
#
# Copyright 2019 Philip Colmer, Linaro Ltd

import znc
import os
import shutil


class deluserdir(znc.Module):
    description = (
        "Deletes or moves user directories to trash when a user account "
        "is deleted"
    )
    module_types = [znc.CModInfo.GlobalModule]
    has_args = True

    def OnLoad(self, args, message):
        success = True
        # Check the args and store associated values
        arglist = args.split()
        for arg in arglist:
            k, v = arg.split("=")
            if k == "trashdir":
                self.nv[k] = v
            else:
                message.s = (
                    "'%s' is not recognised" % k
                )
                success = False
        if "trashdir" not in self.nv:
            message.s = (
                "'trashdir' must be set either to an empty string or"
                " to the desired trash directory"
            )
            success = False
        # If trashdir is specified ...
        if success and self.nv["trashdir"] != "":
            # make sure it exists
            if not os.path.isdir(self.nv["trashdir"]):
                message.s = (
                    "The specified trash directory ('%s') cannot be found" %
                    self.nv["trashdir"]
                )
                success = False
            else:
                # make sure that we can write to it.
                success = os.access(
                    self.nv["trashdir"],
                    os.R_OK | os.W_OK | os.X_OK
                )
                if not success:
                    message.s = (
                        "The specified trash directory ('%s') doesn't have the"
                        " correct access rights for the account running ZNC" %
                        self.nv["trashdir"]
                    )

        if success:
            if self.nv["trashdir"] == "":
                znc.CZNC.Get().Broadcast(
                    "deluserdir is loaded. User directories will be deleted"
                )
            else:
                znc.CZNC.Get().Broadcast(
                    "deluserdir is loaded. User directories will be moved"
                    " to '%s' when user accounts are deleted" %
                    self.nv["trashdir"]
                )
        return success

    def OnDeleteUser(self, user):
        trashdir = self.nv["trashdir"]
        userdir = user.GetUserPath()
        try:
            if trashdir == "":
                znc.CZNC.Get().Broadcast("Deleting %s" % userdir)
                shutil.rmtree(userdir)
            else:
                znc.CZNC.Get().Broadcast("Moving %s to trash dir" % userdir)
                shutil.move(userdir, trashdir)
            self.__output_users(True)
        except Exception as e:
            znc.CZNC.Get().Broadcast(
                "deluserdir:OnDeleteUser failed with %s" % str(e))
        return znc.CONTINUE

    def __output_table(self, t, broadcast):
        i = 0
        s = znc.String()
        while t.GetLine(i, s):
            if broadcast:
                znc.CZNC.Get().Broadcast(s.s)
            else:
                self.PutModule(s.s)
            i += 1

    def __output_users(self, broadcast):
        try:
            dirs = next(os.walk(znc.CZNC.Get().GetUserPath()))[1]
            # Create a table with all of the user directories list
            t = znc.CTable()
            t.AddColumn("Users with directories")
            for dir in dirs:
                t.AddRow()
                t.SetCell("Users with directories", dir)
            self.__output_table(t, broadcast)
        except Exception as e:
            self.PutModule(
                "__output_users failed with %s" % str(e))

    def OnModCommand(self, message):
        # For now, just provide some debugging information when we receive
        # a private message.
        self.__output_users(False)
