# This module extends ZNC so that, when a user account is deleted, the
# corresponding user directory is either deleted or moved to a designated
# trash directory.
#
# Copyright 2019 Philip Colmer, Linaro Ltd

import znc
import os


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
                self.PutModule(
                    "'%s' is not recognised" % k
                )
                success = False
        if "trashdir" not in self.nv:
            self.PutModule(
                "'trashdir' must be set either to an empty string or"
                " to the desired trash directory"
            )
            success = False
        # If trashdir is specified ...
        if success and self.nv["trashdir"] != "":
            # make sure it exists
            if not os.path.isdir(self.nv["trashdir"]):
                self.PutModule(
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
                    self.PutModule(
                        "The specified trash directory ('%s') doesn't have the"
                        " correct access rights for the account running ZNC" %
                        self.nv["trashdir"]
                    )

        if success:
            if self.nv["trashdir"] == "":
                self.PutModule(
                    "deluserdir is loaded. User directories will be deleted"
                )
            else:
                self.PutModule(
                    "deluserdir is loaded. User directories will be moved"
                    " to '%s' when user accounts are deleted" %
                    self.nv["trashdir"]
                )
        return success
