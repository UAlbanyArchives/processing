from datetime import datetime
from subprocess import Popen, PIPE

class Package:

    def copyRsync(self, source, destination, retry=0):
        retry += 1
        if retry < 6:
            cmd = ["rsync", "-arv", "--partial", source, destination]
            print ("Copy attempt " + str(retry) + " at " + str(datetime.now()))
            print ("Running " + " ".join(cmd))
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print (stdout.decode())
                print (stderr.decode())
                print ("Copy failed at " + str(datetime.now()))
                print ("Retrying...")
                self.copyRsync(source, destination, retry)
            else:
                print ("Success!")
                print ("Copy completed at " + str(datetime.now()))
                print (stdout.decode())
                if len(stderr) > 0:
                    print (stderr.decode())
        else:
            print ("Failed to copy in 5 attempts")
            raise ValueError("Failed to copy in 5 attempts")