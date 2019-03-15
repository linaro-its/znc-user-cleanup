# This module extends ZNC so that, when a user account is deleted, the
# corresponding user directory is either deleted or moved to a designated
# trash directory.
#
# Copyright 2019 Philip Colmer, Linaro Ltd

import znc
import os
# import shutil
import subprocess


class deluserdir(znc.Module):
    description = (
        "Deletes or moves user directories to trash when a user account "
        "is deleted"
    )
    module_types = [znc.CModInfo.GlobalModule]

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
                print(
                    "deluserdir is loaded. User directories will be deleted"
                )
            else:
                print(
                    "deluserdir is loaded. User directories will be moved"
                    " to '%s' when user accounts are deleted" %
                    self.nv["trashdir"]
                )
        return success

    def run_command(self, cmd):
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if stdoutdata == "" and stderrdata == "":
            return True
        else:
            if stdoutdata != "":
                print(stdoutdata)
            if stderrdata != "":
                print(stderrdata)
            return False

    def OnDeleteUser(self, user):
        trashdir = self.nv["trashdir"]
        userdir = user.GetUserPath()
        try:
            if trashdir == "":
                print("Deleting %s" % userdir)
                if self.run_command(["rm", "-rf", userdir]):
                    print("Deletion completed")
                # shutil.rmtree(userdir)
            else:
                print("Moving %s to trash dir" % userdir)
                if self.run_command(["mv", userdir, trashdir]):
                    print("Move completed")
                # shutil.move(userdir, trashdir)
        except Exception as e:
            print("OnDeleteUser failed with %s" % str(e))
        return znc.CONTINUE
