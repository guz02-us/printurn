import cmd, printcore, sys 
#help(cmd)
import glob, os, time
if os.name=="nt":
    try:
        import _winreg
    except:
        pass
READLINE=True
try:
    import readline
    try:
        readline.rl.mode.show_all_if_ambiguous="on" #config pyreadline on windows
    except:
        pass
except:
    READLINE=False #neither readline module is available

def dosify(name):
    return os.path.split(name)[1].split(".")[0][:8]+".g"


class pronsole(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        if not READLINE:
            self.completekey=None
        self.p=printcore.printcore()
        self.p.recvcb=self.recvcb
        self.recvlisteners=[]
        self.prompt="PC>"
        self.p.onlinecb=self.online
        self.f=None
        self.listing=0
        self.sdfiles=[]
        self.paused=False
        self.sdprinting=0
        self.temps={"pla":"210","abs":"230","off":"0"}
        self.bedtemps={"pla":"60","abs":"110","off":"0"}
        self.percentdone=0
        self.tempreadings=""
        self.aliases={}
        
    def scanserial(self):
        """scan for available ports. return a list of device names."""
        baselist=[]
        if os.name=="nt":
            try:
                key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM")
                i=0
                while(1):
                    baselist+=[_winreg.EnumValue(key,i)[1]]
                    i+=1
            except:
                pass

        return baselist+glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') +glob.glob("/dev/tty.*")+glob.glob("/dev/cu.*")+glob.glob("/dev/rfcomm*")

    def online(self):
        print "Printer is now online"
        sys.stdout.write(self.prompt)
        sys.stdout.flush()
    
    def help_help(self,l):
        self.do_help("")
    
    def do_gcodes(self,l):
        self.help_gcodes()
    
    def help_gcodes(self):
        print "Gcodes are passed through to the printer as they are"
    
    def do_alias(self,l):
        if l == "":
            # list aliases
            if len(self.aliases):
                self.print_topics("Aliases, to display type: alias <name>",self.aliases.keys(),15,80)
            else:
                print "No aliases defined, to define see: help alias"
            return
        alias_l = l.split(None,1)
        alias_name = alias_l[0]
        if len(alias_l) < 2:
            # display alias
            if alias_name in self.aliases.keys():
                print "Alias '"+alias_name+"' stands for '"+self.aliases[alias_name]+"'"
            else:
                print "Alias '"+alias_name+"' is not defined"
            return
        alias_name,alias_def = alias_l
        if alias_def.lower() == "/d":
            # delete alias
            if alias_name in self.aliases.keys():
                delattr(self.__class__,"do_"+alias_name)
                del self.aliases[alias_name]
                print "Alias '"+alias_name+"' removed"
                return
            else:
                print "Alias '"+alias_name+"' is not defined"
            return
        # (re)define an alias
        if alias_name not in self.aliases.keys() and hasattr(self.__class__,"do_"+alias_name):
            print "Name '"+alias_name+"' is already being used by built-in command"
            return
        func = lambda self,args,alias_def=alias_def: self.onecmd(" ".join((alias_def,args)))
        self.aliases[alias_name] = alias_def
        setattr(self.__class__,"do_"+alias_name,func)
        setattr(self.__class__,"help_"+alias_name,lambda self=self,alias_name=alias_name: self.subhelp_alias(alias_name))
    
    def help_alias(self):
        print "Create/modify/view aliases: alias <name> [<command>]"
        print "if <command> is not specified, displays the alias definition"
        print "without arguments, displays list of all defined aliases"
        print "To remove an alias: alias <name> /d"
        
    def complete_alias(self,text,line,begidx,endidx):
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in self.aliases.keys() if i.startswith(text)]
        elif(len(line.split())==3 or (len(line.split())==2 and line[-1]==" ")):
            return self.completenames(text)
        else:
            return []
    
    def subhelp_alias(self,alias_name):
        print "'"+alias_name+"' is alias for '"+self.aliases[alias_name]+"'"
    
    def postloop(self):
        self.p.disconnect()
        cmd.Cmd.postloop(self)
    
    def preloop(self):
        try:
            with open(os.path.join(os.path.expanduser("~"),".pronsolerc")) as rc:
                for rc_cmd in rc:
                    if not rc_cmd.lstrip().startswith("#"):
                        self.onecmd(rc_cmd)
        except IOError:
            pass
        print "Welcome to the printer console! Type \"help\" for a list of available commands."
        cmd.Cmd.preloop(self)
    
    def do_connect(self,l):
        a=l.split()
        p=self.scanserial()
        port=None
        if len(p)>0:
            port=p[0] 
        baud=115200
        if(len(a)>0):
            port=a[0]
        if(len(a)>1):
            try:
                baud=int(a[1])
            except:
                pass
        if len(p)==0 and port is None:
            print "No serial ports detected - please specify a port"
            return
        if len(a)==0:
            print "No port specified - connecting to %s at %dbps" % (port,baud)
        self.p.connect(port, baud)
    
    def help_connect(self):
        print "Connect to printer"
        print "connect <port> <baudrate>"
        print "If port and baudrate are not specified, connects to first detected port at 115200bps"
        ports=self.scanserial()
        if(len(ports)):
            print "Available ports: ", " ".join(ports)
        else:
            print "No serial ports were automatically found."
    
    def complete_connect(self, text, line, begidx, endidx):
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in self.scanserial() if i.startswith(text)]
        elif(len(line.split())==3 or (len(line.split())==2 and line[-1]==" ")):
            return [i for i in ["2400", "9600", "19200", "38400", "57600", "115200"] if i.startswith(text)]
        else:
            return []
    
    def do_disconnect(self,l):
        self.p.disconnect()
        
    def help_disconnect(self):
        print "Disconnects from the printer"
    
    def do_load(self,l):
        if len(l)==0:
            print "No file name given."
            return
        print "Loading file:"+l
        if not(os.path.exists(l)):
            print "File not found!"
            return
        self.f=[i.replace("\n","") for i in open(l)]
        self.filename=l
        print "Loaded ",l,", ",len(self.f)," lines."
        
    def complete_load(self, text, line, begidx, endidx):
        s=line.split()
        if len(s)>2:
            return []
        if (len(s)==1 and line[-1]==" ") or (len(s)==2 and line[-1]!=" "):
            if len(s)>1:
                return [i[len(s[1])-len(text):] for i in glob.glob(s[1]+"*/")+glob.glob(s[1]+"*.g*")]
            else:
                return glob.glob("*/")+glob.glob("*.g*")
                
    def help_load(self):
        print "Loads a gcode file (with tab-completion)"
    
    
    def do_upload(self,l):
        if len(l)==0:
            print "No file name given."
            return
        print "Loading file:"+l.split()[0]
        if not(os.path.exists(l.split()[0])):
            print "File not found!"
            return
        if not self.p.online:
            print "Not connected to printer."
            return
        self.f=[i.replace("\n","") for i in open(l.split()[0])]
        self.filename=l.split()[0]
        print "Loaded ",l,", ",len(self.f)," lines."
        tname=""
        if len(l.split())>1:
            tname=l.split()[1]
        else:
            print "please enter target name in 8.3 format."
            return
        print "Uploading as ",tname
        print("Uploading "+self.filename)
        self.p.send_now("M28 "+tname)
        print("Press Ctrl-C to interrupt upload.")
        self.p.startprint(self.f)
        try:
            sys.stdout.write("Progress: 00.0%")
            sys.stdout.flush()
            time.sleep(1)
            while self.p.printing:
                time.sleep(1)
                sys.stdout.write("\b\b\b\b\b%04.1f%%" % (100*float(self.p.queueindex)/len(self.p.mainqueue),) )
                sys.stdout.flush()
            self.p.send_now("M29 "+tname)
            self.sleep(0.2)
            self.p.clear=1
            self.listing=0
            self.sdfiles=[]
            self.recvlisteners+=[self.listfiles]
            self.p.send_now("M20")
            time.sleep(0.5)
            print "\b\b\b\b\b100%. Upload completed. ",tname," should now be on the card."
            return
        except:
            print "...interrupted!"
            self.p.pause()
            self.p.send_now("M29 "+tname)
            time.sleep(0.2)
            self.p.clear=1
            self.p.startprint([])
            print "A partial file named ",tname," may have been written to the sd card."
    
    
    def complete_upload(self, text, line, begidx, endidx):
        s=line.split()
        if len(s)>2:
            return []
        if (len(s)==1 and line[-1]==" ") or (len(s)==2 and line[-1]!=" "):
            if len(s)>1:
                return [i[len(s[1])-len(text):] for i in glob.glob(s[1]+"*/")+glob.glob(s[1]+"*.g*")]
            else:
                return glob.glob("*/")+glob.glob("*.g*")
        
    def help_upload(self):
        print "Uploads a gcode file to the sd card"
    
    
    def help_print(self):
        if self.f is None:
            print "Send a loaded gcode file to the printer. Load a file with the load command first."
        else:
            print "Send a loaded gcode file to the printer. You have "+self.filename+" loaded right now."
    
    def do_print(self, l):
        if self.f is None:
            print "No file loaded. Please use load first."
            return
        if not self.p.online:
            print "Not connected to printer."
            return
        print("Printing "+self.filename)
        print("You can monitor the print with the monitor command.")
        self.p.startprint(self.f)
        #self.p.pause()
        #self.paused=True
        #self.do_resume(None)
        
    def do_pause(self,l):
        if self.sdprinting:
            self.p.send_now("M25")
        else:
            if(not self.p.printing):
                print "Not printing, cannot pause."
                return
            self.p.pause()
            self.p.connect()# This seems to work, but is not a good solution. 
        self.paused=True
        
        #self.do_resume(None)
        
    def help_pause(self,l):
        print "Pauses a running print"
        
    def do_resume(self,l):
        if not self.paused:
            print "Not paused, unable to resume. Start a print first."
            return
        self.paused=False
        if self.sdprinting:
            self.p.send_now("M24")
            return
        else:
            self.p.resume()
        return
        try:
            self.p.resume()
            #print self.p.printing
            sys.stdout.write("Progress: 00.0%")
            sys.stdout.flush()
            time.sleep(1)
            while self.p.printing:
                time.sleep(1)
                sys.stdout.write("\b\b\b\b\b%04.1f%%" % (100*float(self.p.queueindex)/len(self.p.mainqueue),) )
                sys.stdout.flush()
            print "\b\b\b\b\b100%. Print completed."
            return
        except:
            print "...interrupted!"
            self.paused=True
            self.p.pause()
            print "Use the resume command to resume this print"
    
    def help_resume(self):
        print "Resumes a paused print."
    
    def emptyline(self):
        pass
        
    def do_shell(self,l):
        exec(l)
    
    def listfiles(self,line):
        if "Begin file list" in line:
            self.listing=1
        elif "End file list" in line:
            self.listing=0
            self.recvlisteners.remove(self.listfiles)
        elif self.listing:
            self.sdfiles+=[line.replace("\n","").replace("\r","").lower()]
        
    def do_ls(self,l):
        if not self.p.online:
            print "Printer is not online. Try connect to it first."
            return
        self.listing=0
        self.sdfiles=[]
        self.recvlisteners+=[self.listfiles]
        self.p.send_now("M20")
        time.sleep(0.5)
        print " ".join(self.sdfiles)
    
    def help_ls(self):
        print "lists files on the SD card"
        
    def waitforsdresponse(self,l):
        if "file.open failed" in l:
            print "Opening file failed."
            self.recvlisteners.remove(self.waitforsdresponse)
            return
        if "File opened" in l:
            print l
        if "File selected" in l:
            print "Starting print"
            self.p.send_now("M24")
            self.sdprinting=1
            #self.recvlisteners.remove(self.waitforsdresponse)
            return
        if "Done printing file" in l:
            print l
            self.sdprinting=0
            self.recvlisteners.remove(self.waitforsdresponse)
            return
        if "SD printing byte" in l:
            #M27 handler
            try:
                resp=l.split()
                vals=resp[-1].split("/")
                self.percentdone=100.0*int(vals[0])/int(vals[1])
            except:
                pass
        
    def do_sdprint(self,l):
        if not self.p.online:
            print "Printer is not online. Try connect to it first."
            return
        self.listing=0
        self.sdfiles=[]
        self.recvlisteners+=[self.listfiles]
        self.p.send_now("M20")
        time.sleep(0.5)
        if not (l.lower() in self.sdfiles):
            print "File is not present on card. Upload it first"
            return
        self.recvlisteners+=[self.waitforsdresponse]
        self.p.send_now("M23 "+l.lower())
        print "Printing file: "+l.lower()+" from SD card."
        print "Requesting SD print..."
        time.sleep(1)
        
    def help_sdprint(self):
        print "Print a file from the SD card. Tabcompletes with available file names."
        print "sdprint filename.g"
        
    def complete_sdprint(self, text, line, begidx, endidx):
        if self.sdfiles==[] and self.p.online:
            self.listing=0
            self.recvlisteners+=[self.listfiles]
            self.p.send_now("M20")
            time.sleep(0.5)
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in self.sdfiles if i.startswith(text)]
            
    def recvcb(self,l):
        if "T:" in l:
            self.tempreadings=l
        for i in self.recvlisteners:
            i(l)
    
    def help_shell(self):
        print "Executes a python command. Example:"
        print "! os.listdir('.')"
        
    def default(self,l):
        if(l[0]=='M' or l[0]=="G"):
            if(self.p and self.p.online):
                print "SENDING:"+l
                self.p.send_now(l)
            else:
                print "Printer is not online."
            return
        if(l[0]=='m' or l[0]=="g"):
            if(self.p and self.p.online):
                print "SENDING:"+l.upper()
                self.p.send_now(l.upper())
            else:
                print "Printer is not online."
            return
        else:
            cmd.Cmd.default(self,l)
    
    def help_help(self):
        self.do_help("")
    
    def tempcb(self,l):
        if "ok T:" in l:
            print l.replace("\r","").replace("T","Hotend").replace("B","Bed").replace("\n","").replace("ok ","")
            self.recvlisteners.remove(self.tempcb)
        
    def do_gettemp(self,l):
        if self.p.online:
            self.recvlisteners+=[self.tempcb]
            self.p.send_now("M105")
            time.sleep(0.5)
    
    def help_gettemp(self):
        print "Read the extruder and bed temperature."
    
    def do_settemp(self,l):
        try:
            l=l.lower().replace(",",".").replace("abs","230").replace("pla","210").replace("off","0")
            f=float(l)
            if f>=0:
                if self.p.online:
                    self.p.send_now("M104 S"+l)
                    print "Setting hotend temperature to ",f," degrees Celsius."
                else:
                    print "Printer is not online."
            else:
                print "You cannot set negative temperatures. To turn the hotend off entirely, set its temperature to 0."
        except:
            print "You must enter a temperature."
            
    def help_settemp(self):
        print "Sets the hotend temperature to the value entered."
        print "Enter either a temperature in celsius or one of the following keywords"
        print ", ".join([i+"("+self.temps[i]+")" for i in self.temps.keys()])
    
    def complete_settemp(self, text, line, begidx, endidx):
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in self.temps.keys() if i.startswith(text)]
    
    def do_bedtemp(self,l):
        try:
            l=l.lower().replace(",",".").replace("abs","110").replace("pla","65").replace("off","0")
            f=float(l)
            if f>=0:
                if self.p.online:
                    self.p.send_now("M140 S"+l)
                    print "Setting bed temperature to ",f," degrees Celsius."
                else:
                    print "Printer is not online."
            else:
                print "You cannot set negative temperatures. To turn the bed off entirely, set its temperature to 0."
        except:
            print "You must enter a temperature."
            
    def help_bedtemp(self):
        print "Sets the bed temperature to the value entered."
        print "Enter either a temperature in celsius or one of the following keywords"
        print ", ".join([i+"("+self.bedtemps[i]+")" for i in self.bedtemps.keys()])
        
    def complete_bedtemp(self, text, line, begidx, endidx):
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in self.bedtemps.keys() if i.startswith(text)]
    
    def do_move(self,l):
        if(len(l.split())<2):
            print "No move specified."
            return
        if self.p.printing:
            print "Printer is currently printing. Please pause the print before you issue manual commands."
            return
        if not self.p.online:
            print "Printer is not online. Unable to move."
            return
        feed=300
        axis="E"
        l=l.split()
        if(l[0].lower()=="x"):
            feed=3000
            axis="X"
        elif(l[0].lower()=="y"):
            feed=3000
            axis="Y"
        elif(l[0].lower()=="z"):
            feed=200
            axis="Z"
        elif(l[0].lower()=="e"):
            feed=300
            axis="E"
        else:
            print "Unknown axis."
            return
        dist=0
        try:
            dist=float(l[1])
        except:
            print "Invalid number"
            return
        self.p.send_now("G91")
        self.p.send_now("G1 "+axis+str(l[1])+" F"+str(feed))
        self.p.send_now("G90")
        
    def help_move(self):
        print "Move an axis. Specify the name of the axis and the amount. "
        print "move X 10 will move the X axis forward by 10mm"
        print "move Z -1 will move the Z axis down by 1mm"
        print "Common amounts are in the tabcomplete list."
    
    def complete_move(self, text, line, begidx, endidx):
        if (len(line.split())==2 and line[-1] != " ") or (len(line.split())==1 and line[-1]==" "):
            return [i for i in ["X ","Y ","Z ","E "] if i.lower().startswith(text)]
        elif(len(line.split())==3 or (len(line.split())==2 and line[-1]==" ")):
            base=line.split()[-1]
            rlen=0
            if base.startswith("-"):
                rlen=1
            if line[-1]==" ":
                base=""
            return [i[rlen:] for i in ["-100","-10","-1","-0.1","100","10","1","0.1","-50","-5","-0.5","50","5","0.5","-200","-20","-2","-0.2","200","20","2","0.2"] if i.startswith(base)]
        else:
            return []
    
    def do_extrude(self,l,override=None,overridefeed=300):
        length=5#default extrusion length
        feed=300#default speed
        if not self.p.online:
            print "Printer is not online. Unable to move."
            return
        if self.p.printing:
            print "Printer is currently printing. Please pause the print before you issue manual commands."
            return
        ls=l.split()
        if len(ls):
            try:
                length=float(ls[0])
            except:
                print "Invalid length given."
        if len(ls)>1:
            try:
                feed=int(ls[1])
            except:
                print "Invalid speed given."
        if override is not None:
            length=override
            feed=overridefeed
        if length > 0:
            print "Extruding %fmm of filament."%(length,)
        elif length <0:
            print "Reversing %fmm of filament."%(-1*length,)
        else:
            "Length is 0, not doing anything."
        self.p.send_now("G91")
        self.p.send_now("G1 E"+str(length)+" F"+str(feed))
        self.p.send_now("G90")
        
    def help_extrude(self):
        print "Extrudes a length of filament, 5mm by default, or the number of mm given as a parameter"
        print "extrude - extrudes 5mm of filament at 300mm/min (5mm/s)"
        print "extrude 20 - extrudes 20mm of filament at 300mm/min (5mm/s)"
        print "extrude -5 - REVERSES 5mm of filament at 300mm/min (5mm/s)"
        print "extrude 10 210 - extrudes 10mm of filament at 210mm/min (3.5mm/s)"
        
    def do_reverse(self, l):
        length=5#default extrusion length
        feed=300#default speed
        if not self.p.online:
            print "Printer is not online. Unable to move."
            return
        if self.p.printing:
            print "Printer is currently printing. Please pause the print before you issue manual commands."
            return
        ls=l.split()
        if len(ls):
            try:
                length=float(ls[0])
            except:
                print "Invalid length given."
        if len(ls)>1:
            try:
                feed=int(ls[1])
            except:
                print "Invalid speed given."
        self.do_extrude("",length*-1.0,feed)
        
    def help_reverse(self):
        print "Reverses the extruder, 5mm by default, or the number of mm given as a parameter"
        print "reverse - reverses 5mm of filament at 300mm/min (5mm/s)"
        print "reverse 20 - reverses 20mm of filament at 300mm/min (5mm/s)"
        print "reverse 10 210 - extrudes 10mm of filament at 210mm/min (3.5mm/s)"
        print "reverse -5 - EXTRUDES 5mm of filament at 300mm/min (5mm/s)"
    
    def do_exit(self,l):
        print "Disconnecting from printer..."
        self.p.disconnect()
        print "Exiting program. Goodbye!"
        return True
        
    def help_exit(self):
        print "Disconnects from the printer and exits the program."
    
    def do_monitor(self,l):
        interval=5
        if not self.p.online:
            print "Printer is not online. Please connect first."
            return
        print "Monitoring printer, use ^C to interrupt."
        if len(l):
            try:
                interval=float(l)
            except:
                print "Invalid period given."
        print "Updating values every %f seconds."%(interval,)
        try:
            while(1):
                self.p.send_now("M105")
                if(self.sdprinting):
                    self.p.send_now("M27")
                print (self.tempreadings.replace("\r","").replace("T","Hotend").replace("B","Bed").replace("\n","").replace("ok ",""))
                if(self.p.printing):
                    print "Print progress: ", 100*float(self.p.queueindex)/len(self.p.mainqueue), "%"
                
                if(self.sdprinting):
                    print "SD print progress: ", self.percentdone,"%"
                time.sleep(interval)
        except:
            print "Done monitoring."
            pass
            
    def help_monitor(self):
        print "Monitor a machine's temperatures and an SD print's status."
        print "monitor - Reports temperature and SD print status (if SD printing) every 5 seconds"
        print "monitor 2 - Reports temperature and SD print status (if SD printing) every 2 seconds"
        
    def do_skein(self,l):
        l=l.split()
        if len(l)==0:
            print "No file name given."
            return
        settings=0
        if(l[0]=="set"):
            settings=1
        else:
            print "Skeining file:"+l[0]
            if not(os.path.exists(l[0])):
                print "File not found!"
                return
        if not os.path.exists("skeinforge"):
            print "Skeinforge not found. \nPlease copy Skeinforge into a directory named \"skeinforge\" in the same directory as this file."
            return
        if not os.path.exists("skeinforge/__init__.py"):
            with open("skeinforge/__init__.py","w"):
                pass
        try:
            from skeinforge.skeinforge_application.skeinforge_utilities import skeinforge_craft
            from skeinforge.skeinforge_application import skeinforge
            if(settings):
                skeinforge.main()
            else:
                if(len(l)>1):
                    if(l[1] == "view"):
                        skeinforge_craft.writeOutput(l[0],True)
                    else:
                        skeinforge_craft.writeOutput(l[0],False)
                else:
                    skeinforge_craft.writeOutput(l[0],False)
                print "Loading skeined file."
                self.do_load(l[0].replace(".stl","_export.gcode"))
        except:
            print "Skeinforge execution failed."
        
    def complete_skein(self, text, line, begidx, endidx):
        s=line.split()
        if len(s)>2:
            return []
        if (len(s)==1 and line[-1]==" ") or (len(s)==2 and line[-1]!=" "):
            if len(s)>1:
                return [i[len(s[1])-len(text):] for i in glob.glob(s[1]+"*/")+glob.glob(s[1]+"*.stl")]
            else:
                return glob.glob("*/")+glob.glob("*.stl")
                
    def help_skein(self):
        print "Creates a gcode file from an stl model using skeinforge (with tab-completion)"
        print "skein filename.stl - create gcode file"
        print "skein filename.stl view - create gcode file and view using skeiniso"
        print "skein set - adjust skeinforge settings"
        
    
interp=pronsole()
try:
    interp.cmdloop()
except:
    interp.p.disconnect()
    raise
