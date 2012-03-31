#!/usr/bin/env xmipp_python
'''
/***************************************************************************
 * Authors:     J.M. de la Rosa Trevin (jmdelarosa@cnb.csic.es)
 *
 *
 * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307  USA
 *
 *  All comments concerning this program package may be sent to the
 *  e-mail address 'xmipp@cnb.csic.es'
 ***************************************************************************/
 '''

import os
import Tkinter as tk
#import protlib_gui_figure
from protlib_gui import ProtocolGUI, Fonts, registerCommonFonts
from protlib_gui_ext import ToolTip, centerWindows, askYesNo, showInfo, XmippTree, \
    showBrowseDialog, showTextfileViewer, showError, TaggedText, XmippButton, ProjectLabel,\
    FlashMessage, showWarning, YesNoDialog, getXmippImage
from config_protocols import *
from protlib_base import XmippProject, getExtendedRunName
from protlib_utils import ProcessManager,  getHostname
from protlib_sql import SqliteDb, ProgramDb
from protlib_filesystem import getXmippPath

# Redefine BgColor
BgColor = "white"

ACTION_DELETE = 'Delete'
ACTION_EDIT = 'Edit'
ACTION_COPY = 'Copy'
ACTION_REFRESH = 'Refresh'
ACTION_DEFAULT = 'Default'
GROUP_ALL = 'All'
GROUP_XMIPP = protDict.xmipp.title
        
class ProjectSection(tk.Frame):
    def __init__(self, master, label_text, **opts):
        tk.Frame.__init__(self, master, bd=2)
        self.config(**opts)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.label = ProjectLabel(self, text=label_text)
        self.label.grid(row=0, column=0, sticky='sw')
        self.frameButtons = tk.Frame(self)
        self.frameButtons.grid(row=0, column=1, sticky='e')
        self.frameContent = tk.Frame(self)
        self.frameContent.grid(row=1, column=0, columnspan=2, sticky='nsew')
        
    def addButton(self, text, imagePath=None, **opts):
        btn = XmippButton(self.frameButtons, text, imagePath, **opts)
        btn.pack(side=tk.LEFT, padx=5)
        return btn
    
    def addWidget(self, Widget, **opts):
        w = Widget(self.frameButtons, **opts)
        w.pack(side=tk.LEFT, padx=5)
        return w
    
    def displayButtons(self, show=True):
        if show:
            self.frameButtons.grid()
        else:
            self.frameButtons.grid_remove()
            
class ProjectButtonMenu(tk.Frame):
    def __init__(self, master, label_text, **opts):
        tk.Frame.__init__(self, master, **opts)
        self.label = ProjectLabel(self, text=label_text)
        self.label.pack(padx=5, pady=(5, 0))
        
    def addButton(self, button_text, **opts):
        btn = XmippButton(self, button_text, **opts)
        btn.pack(fill=tk.X, padx=5, pady=(5, 0))
        return btn
        
class XmippProjectGUI():  
    def __init__(self, project):
        self.project = project
        #self.pm = ProcessManager()
        
    def cleanProject(self):
        if askYesNo("DELETE confirmation", "You are going to <DELETE ALL> project data (runs, logs, results...)\nDo you really want to continue?", self.root):
            self.project.clean()
            self.close()
            
    def deleteTmpFiles(self):
        try:
            self.project.deleteTmpFiles()
            showInfo("Operation success", "All temporary files have been successfully removed", self.root)
        except Exception, e:
            showError("Operation error ", str(e), self.root)
    
    def browseFiles(self):
        showBrowseDialog(parent=self.root, seltype="none", selmode="browse")
        
    def initVariables(self):
        self.ToolbarButtonsDict = {}
        self.runButtonsDict = {}
        self.lastDisplayGroup = None
        self.lastRunSelected = None
        self.lastMenu = None
        self.Frames = {}
        self.historyRefresh = None
        self.historyRefreshRate = 4 # Refresh rate will be 1, 2, 4 or 8 seconds
        ## Create some icons
        self.images = {}
        ## This are images icons for each run_state
        paths = ['save_small', 'select_run', 'progress_none', 
                 'progress_ok', 'progress_error', 'level_warning']
        for i, path in enumerate(paths):
            self.images[i] = getXmippImage(path + '.gif')
            
    def getImage(self, path):
        return self.images[path]
              
    def addBindings(self):
        #self.root.bind('<Configure>', self.unpostMenu)
        #self.root.bind("<Unmap>", self.unpostMenu)
        #self.root.bind("<Map>", self.unpostMenu)
        #self.Frames['main'].bind("<Leave>", self.unpostMenu)
        self.root.bind('<FocusOut>', self.unpostMenu)
        self.root.bind('<Button-1>', self.unpostMenu)
        self.root.bind('<Return>', lambda e: self.runButtonClick(ACTION_DEFAULT))
        self.root.bind('<Control_L><Return>', lambda e: self.runButtonClick(ACTION_COPY))
        self.root.bind('<Alt_L><e>', lambda e: self.runButtonClick(ACTION_EDIT))
        self.root.bind('<Alt_L><d>', lambda e: self.runButtonClick(ACTION_COPY))
        self.root.bind('<Delete>', lambda e: self.runButtonClick(ACTION_DELETE))
        self.root.bind('<Up>', self.lbHist.selection_up)
        self.root.bind('<Down>', self.lbHist.selection_down)
        self.root.bind('<Alt_L><c>', self.close )
        self.root.bind('<Alt_L><o>', self.showOutput)
        self.root.bind('<Alt_L><a>', self.visualizeRun)
        
    def createMainMenu(self):
        self.menubar = tk.Menu(self.root)
        #Project menu
        self.menuProject = tk.Menu(self.root, tearoff=0)
        self.menubar.add_cascade(label="Project", menu=self.menuProject)
        self.browseFolderImg = tk.PhotoImage(file=getXmippPath('resources', 'folderopen.gif'))
        self.menuProject.add_command(label="Browse files", command=self.browseFiles, 
                                     image=self.browseFolderImg, compound=tk.LEFT)
        self.delImg = tk.PhotoImage(file=getXmippPath('resources', 'delete.gif'))
        self.menuProject.add_command(label="Remove temporary files", command=self.deleteTmpFiles,
                                     image=self.delImg, compound=tk.LEFT) 
        self.cleanImg = tk.PhotoImage(file=getXmippPath('resources', 'clean.gif'))       
        self.menuProject.add_command(label="Clean project", command=self.cleanProject,
                                     image=self.cleanImg, compound=tk.LEFT)
        self.menuProject.add_separator()
        self.menuProject.add_command(label="Exit", command=self.close)
        
    def selectRunUpDown(self, event):
        if event.keycode == 111: # Up arrow
            self.lbHist.selection_move_up()
        elif event.keycode == 116: # Down arrow
            self.lbHist.selection_move_down()
        
    def createToolbarMenu(self, parent, opts=[]):
        if len(opts) > 0:
            menu = tk.Menu(parent, bg=ButtonBgColor, activebackground=ButtonBgColor, font=Fonts['button'], tearoff=0)
            prots = [protDict[o] for o in opts]
            for p in prots:
                #Following is a bit tricky, its due Python notion of scope, a for does not define a new scope
                # and menu items command setting
                def item_command(prot): 
                    def new_command(): 
                        self.launchProtocolGUI(self.project.newProtocol(prot.name))
                    return new_command 
                menu.add_command(label=p.title, command=item_command(p))
            menu.bind("<Leave>", self.unpostMenu)
            return menu
        return None

    
    #GUI for launching Xmipp Programs as Protocols        
    def launchProgramsGUI(self, event=None):
        text = protDict.xmipp.title
#        last = self.lastDisplayGroup
#        self.clickToolbarButton(text, False)
#        if text != last and len(self.runs)>0:
#            return
        db = ProgramDb()        
        root = tk.Toplevel()
        root.withdraw()
        root.title(text)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        detailsSection = ProjectSection(root, 'Details')
        txt = tk.Text(detailsSection.frameContent, width=50, height=10,
                        bg=BgColor, bd=1, relief=tk.RIDGE, font=Fonts['normal'])
        txt.pack(fill=tk.BOTH)
        detailsSection.grid(row=1, column=1, sticky='nsew', 
                            padx=5, pady=5)
        #Create programs panel
        progSection = ProjectSection(root, 'Programs')
        lb = tk.Listbox(progSection.frameContent, width=50, height=14,
                        bg=BgColor, bd=1, relief=tk.RIDGE, font=Fonts['normal'])

        def runClick(event=None):
            program_name = lb.get(int(lb.curselection()[0]))
            tmp_script = self.project.projectTmpPath('protocol_program_header.py')
            os.system(program_name + " --xmipp_write_protocol %(tmp_script)s " % locals())
            self.launchProtocolGUI(self.project.createRunFromScript(protDict.xmipp.name, 
                                                                    tmp_script, program_name))
            root.destroy();           
        
        def showSelection(event):
            #lb = event.widget
            program_name = lb.get(int(lb.curselection()[0]))
            program = db.selectProgram(program_name)
            txt.delete(1.0, tk.END)
            desc = program['usage'].splitlines()
            desc = desc[:5]# show max of 5 lines
            for line in desc:
                txt.insert(tk.END, line)
                
        detailsSection.addButton('Run', command=runClick)
        lb.bind('<ButtonRelease-1>', showSelection)
        lb.bind('<Double-Button-1>', runClick)
        lb.pack(fill=tk.BOTH)
        progSection.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        #Create toolbar
        leftFrame = tk.Frame(root)
        leftFrame.grid(row=0, column=0, rowspan=2, sticky='nw', padx=5, pady=5)
        toolbar = tk.Frame(leftFrame, bd=2, relief=tk.RIDGE)
        section = ProjectButtonMenu(toolbar, 'Categories')
        section.pack(fill=tk.X, pady=5)
        categories = db.selectCategories()
        
        def fillListBox(programs):
            lb.delete(0, tk.END)
            for p in programs:
                lb.insert(tk.END, p['name'])
            
        def searchByKeywords(event=None):
            from protlib_xmipp import ProgramKeywordsRank
            keywords = searchVar.get().split()
            progRank = ProgramKeywordsRank(keywords)
            programs = db.selectPrograms()
            # Calculate ranks
            results = []
            for p in programs:
                rank = progRank.getRank(p)
                #Order by insertion sort
                if rank > 0:
                    name = p['name']
                    #self.maxlen = max(self.maxlen, len(name))
                    pos = len(results)
                    for i, e in reversed(list(enumerate(results))):
                        if e['rank'] < rank:
                            pos = i
                        else: break
                    results.insert(pos, {'rank': rank, 'name': name, 'usage': p['usage']})
            fillListBox(results)
            
        for c in categories:
            def addButton(c):
                section.addButton(c['name'], command=lambda:fillListBox(db.selectPrograms(c)))
            addButton(c)  
        toolbar.grid(row=0)
        ProjectLabel(leftFrame, text="Search").grid(row=1, pady=(10,5))
        searchVar = tk.StringVar()
        searchEntry = tk.Entry(leftFrame, textvariable=searchVar, bg=LabelBgColor)
        searchEntry.grid(row=2, sticky='ew')
        searchEntry.bind('<Return>', searchByKeywords)
        centerWindows(root, refWindows=self.root)
        root.deiconify()
        root.mainloop() 

    def launchRunJobMonitorGUI(self, run):
        runName = getExtendedRunName(run)
        script = run['script']
        pm = ProcessManager(run)
        root = tk.Toplevel()
        root.withdraw()
        root.title(script)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        
        def updateAndClose():
            root.destroy()
            self.historyRefreshRate = 1
            self.updateRunHistory(self.lastDisplayGroup)
            
        def stopRun():
            if askYesNo("Confirm action", "Are you sure to <STOP> run execution?" , parent=root):
                #p = pm.getProcessFromPid(run['pid'])
                pm.stopProcessGroup()
                self.project.projectDb.updateRunState(SqliteDb.RUN_ABORTED, run['run_id'])
                updateAndClose()
                
        
        detailsSection = ProjectSection(root, 'Process monitor')
        detailsSection.addButton("Stop run", command=stopRun)
#        txt = tk.Text(detailsSection.frameContent, width=80, height=15,
#                        bg=BgColor, bd=1, relief=tk.RIDGE, font=Fonts['normal'])
#        txt.tag_config('normal', justify=tk.LEFT)
#        txt.tag_config('bold', justify=tk.LEFT, font=Fonts['button'])
#        txt.pack(fill=tk.BOTH)
        cols = ('pid', '%cpu', '%mem', 'command')
        frame = detailsSection.frameContent
        tree = XmippTree(frame, columns=cols)
        for c in cols:
            tree.heading(c, text=c)
            if c != 'command':
                tree.column(c, width=60)
        tree.heading('#0', text='Node')
        tk.Label(frame, text='Process id:', font=Fonts['button']).grid(row=0, column=0, sticky='e')
        tk.Label(frame, text='Elapsed time:', font=Fonts['button']).grid(row=1, column=0, sticky='e')
        labPid = tk.StringVar()
        tk.Label(frame, textvariable=labPid).grid(row=0, column=1, sticky='w')
        labElap = tk.StringVar()
        tk.Label(frame, textvariable=labElap).grid(row=1, column=1, sticky='w')
        tree.grid(row=2, column=0, sticky='nsew', columnspan=2)
        detailsSection.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        def refreshInfo():
            p = pm.getProcessFromPid()
            #txt.delete(1.0, tk.END)
            tree.clear()
            if p:
                labPid.set(p.pid)
                labElap.set(p.etime)
                #line = "Process id    : %(pid)s\nElapsed time  : %(etime)s\n\nSubprocess:\n" % p.info
                #txt.insert(tk.END, line)
                #txt.insert(tk.END, "PID\t ARGS\t CPU(%)\t MEM(%)\n")
                childs = pm.getProcessGroup()
                lastHost = ''
                for c in childs:
                    c.info['pname'] = pname = os.path.basename(c.args.split()[0])
                    if pname not in ['grep', 'python', 'sh', 'bash', 'xmipp_python', 'mpirun']:
                        line = "%(pid)s\t %(pname)s\t %(pcpu)s\t %(pmem)s\n"
                        if c.host != lastHost:
                            #txt.insert(tk.END, "%s\n" % c.host, 'bold')
                            tree.insert('', 'end', c.host, text=c.host)
                            tree.item(c.host, open=True)
                            lastHost = c.host
                        #txt.insert(tk.END, line % c.info, 'normal')
                        tree.insert(lastHost, 'end', values=(c.pid, c.pcpu, c.pmem, pname))
                tree.after(5000, refreshInfo)
            else:
                updateAndClose()
            
        refreshInfo()
        centerWindows(root, refWindows=self.root)
        root.deiconify()
        root.mainloop()
        
        
    def launchProtocolGUI(self, run, visualizeMode=False):
        run['group_name'] = self.lastDisplayGroup
        top = tk.Toplevel()
        gui = ProtocolGUI()
        gui.createGUI(self.project, run, top, 
                      lambda: self.protocolSaveCallback(run), visualizeMode)
        gui.launchGUI()
        
    def protocolSaveCallback(self, run):
        #self.selectToolbarButton(run['group_name'], False)
        if self.lastDisplayGroup in [GROUP_ALL, run['group_name']]:
            self.historyRefreshRate = 1
            self.updateRunHistory(self.lastDisplayGroup)

    def updateRunHistory(self, protGroup, selectFirst=True, checkDead=False):
        #Cancel if there are pending refresh
        tree = self.lbHist
        
        if self.historyRefresh:
            tree.after_cancel(self.historyRefresh)
            self.historyRefresh = None
        runName = None
        
        if not selectFirst:
            item = tree.selection_first()
            runName = tree.item(item, 'text')
        tree.clear()

        if protGroup == GROUP_ALL:
            self.runs = self.project.projectDb.selectRuns()
        else:
            self.runs = self.project.projectDb.selectRuns(protGroup)
        
        if len(self.runs) > 0:
            for run in self.runs:
                state = run['run_state']
                stateStr = SqliteDb.StateNames[state]
                if not state in [SqliteDb.RUN_SAVED, SqliteDb.RUN_FINISHED]:
                    stateStr += " - %d/%d" % self.project.projectDb.getRunProgress(run)
                    if not state in [SqliteDb.RUN_FAILED, SqliteDb.RUN_ABORTED]:
                        if checkDead and not ProcessManager(run).isAlive():
                                self.project.projectDb.updateRunState(SqliteDb.RUN_FAILED, run['run_id'])
                                stateStr = SqliteDb.StateNames[SqliteDb.RUN_FAILED]
                #if state == SqliteDb.RUN_STARTED:
                tree.insert('', 'end', text = '  ' +  getExtendedRunName(run), 
                            image=self.getImage(state),
                            values=(stateStr, run['last_modified']))  
            
            for c in tree.get_children(''):
                if selectFirst or tree.item(c, 'text') == runName:
                    tree.selection_set(c)
                    self.updateRunSelection(tree.index(c))
                    break
            #Generate an automatic refresh after x ms, with x been 1, 2, 4 increasing until 32
            self.historyRefresh = tree.after(self.historyRefreshRate*1000, self.updateRunHistory, protGroup, False)
            self.historyRefreshRate = min(2*self.historyRefreshRate, 32)
        else:
            self.updateRunSelection(-1)

    #---------------- Functions related with Popup menu ----------------------   
#    def lastPair(self):
#        if self.lastDisplayGroup:
#            return  self.ToolbarButtonsDict[self.lastDisplayGroup]
#        return None
        
    def unpostMenu(self, event=None):
        if self.lastMenu:
            self.lastMenu.unpost()
            self.lastMenu = None
        
    def clickToolbarButton(self, index, showMenu=True):
        key, btn, menu = self.ToolbarButtonsDict[index]
        if menu:
            # Post menu
            x, y, w = btn.winfo_x(), btn.winfo_y(), btn.winfo_width()
            xroot, yroot = self.root.winfo_x() + btn.master.winfo_x(), self.root.winfo_y()+ btn.master.winfo_y()
            menu.post(xroot + x + w + 10, yroot + y)
            self.lastMenu = menu
#        if self.lastDisplayGroup and self.lastDisplayGroup != key:
#            lastBtn, lastMenu = self.lastPair()
#            lastBtn.config(bg=ButtonBgColor, activebackground=ButtonActiveBgColor)
#            if lastMenu:
#                lastMenu.unpost()            
#            
#        if self.lastDisplayGroup and showMenu:
            
    def cbDisplayGroupChanged(self, e=None):
        index = self.cbDisplayGroup.current()
        key, btn, menu = self.ToolbarButtonsDict[index]                
        self.selectDisplayGroup(key)
        
    def selectDisplayGroup(self, group=GROUP_ALL):
        '''Change the display group for runs list'''
        #self.selectToolbarButton(group, showMenu=False)
        if not self.lastDisplayGroup or group != self.lastDisplayGroup:
            self.project.config.set('project', 'lastselected', group)
            self.project.writeConfig()
            self.updateRunHistory(group)
#            if self.lastDisplayGroup:
#                btn, menu = self.ToolbarButtonsDict[self.lastDisplayGroup]
#                btn.config(bg=ButtonBgColor, activebackground=ButtonActiveBgColor)
#            if group != GROUP_ALL: # Update buttons backgroud if different from ALL
#                btn, menu = self.ToolbarButtonsDict[group]
#                btn.config(bg=ButtonBgColor, activebackground=ButtonSelectColor)
            self.lastDisplayGroup = group
            
    def updateRunSelection(self, index):
        state = tk.NORMAL
        details = self.Frames['details']
        if index == -1:
            state = tk.DISABLED
            #Hide details
            details.grid_remove()
        else:
            state = tk.NORMAL
            run = self.lastRunSelected
            showButtons = False
            try:
                prot = self.project.getProtocolFromModule(run['script'])
                if os.path.exists(prot.WorkingDir):
                    summary = '\n'.join(prot.summary())
                    showButtons = True
                    wd = "[%s]" % prot.WorkingDir # If exists, create a link to open folder
                else:
                    wd = prot.WorkingDir
                    summary = "This protocol run has not been executed yet"
                
                labels = '<Run>: ' + getExtendedRunName(run) + \
                          '\n<Created>: ' + run['init'] + '   <Modified>: ' + run['last_modified'] + \
                          '\n<Script>: ' + run['script'] + '\n<Directory>: ' + wd + \
                          '\n<Summary>:\n' + summary   
            except Exception, e:
                labels = 'Error creating protocol: <%s>' % str(e)
            self.detailsText.clear()
            self.detailsText.addText(labels)
            details.displayButtons(showButtons)
            details.grid()
        for btn in self.runButtonsDict.values():
            btn.config(state=state)
            
    def runSelectCallback(self, e=None):
        item = self.lbHist.selection_first()
        index = -1
        if item:
            index = self.lbHist.index(item)
            self.lastRunSelected = self.runs[index]
        self.updateRunSelection(index)
            
    def getLastRunDict(self):
        if self.lastRunSelected:
            from protlib_sql import runColumns
            run = dict(zip(runColumns, self.lastRunSelected))
            run['source'] = run['script']        
            return run
        return None
    
    def runButtonClick(self, event=None):
        #FlashMessage(self.root, 'Opening...', delay=1)
        run = self.getLastRunDict()
        if run:
            state = run['run_state']
            if event == ACTION_DEFAULT:
                if state == SqliteDb.RUN_STARTED:
                    self.launchRunJobMonitorGUI(run)
                else:
                    self.launchProtocolGUI(run)
            elif event == ACTION_EDIT:
                self.launchProtocolGUI(run)
            elif event == ACTION_COPY:
                self.launchProtocolGUI(self.project.copyProtocol(run['protocol_name'], run['script']))
            elif event == ACTION_DELETE:
                if state in [SqliteDb.RUN_STARTED, SqliteDb.RUN_LAUNCHED]:
                    showWarning("Delete warning", "This RUN is LAUNCHED or RUNNING, you need to stopped it before delete", parent=self.root) 
                else:
                    if askYesNo("Confirm DELETE", "<ALL DATA> related to this <protocol run> will be <DELETED>. \nDo you really want to continue?", self.root):
                        error = self.project.deleteRun(run)
                        if error is None:
                            self.updateRunHistory(self.lastDisplayGroup)
                        else: 
                            showError("Error deleting RUN", error, parent=self.root)
            elif event == "Visualize":
                pass
            elif event == ACTION_REFRESH:
                self.historyRefreshRate = 1
                self.updateRunHistory(self.lastDisplayGroup, False, True)
        
    def createToolbarFrame(self, parent):
        #Configure toolbar frame
        toolbar = tk.Frame(parent, bd=2, relief=tk.RIDGE)
        
        self.Frames['toolbar'] = toolbar
        self.logo = getXmippImage('xmipp2.gif')
        label = tk.Label(toolbar, image=self.logo)
        label.pack()
        
        #Create toolbar buttons
        #i = 1
        section = None
        self.ToolbarButtonsDict[0] = (GROUP_ALL, None, None)
        index = 1
        for k, v in sections:
            section = ProjectButtonMenu(toolbar, k)
            section.pack(fill=tk.X, pady=5)
            for o in v:
                text = o[0]
                key = "%s_%s" % (k, text)
                opts = o[1:]
                def btn_command(index): 
                    def new_command(): 
                        self.clickToolbarButton(index)
                    return new_command 
                btn = section.addButton(text, command=btn_command(index))
                menu = self.createToolbarMenu(section, opts)
                self.ToolbarButtonsDict[index] = (key, btn, menu)
                index = index + 1
        section.addButton(GROUP_XMIPP, command=self.launchProgramsGUI)
        self.ToolbarButtonsDict[index] = (GROUP_XMIPP, None, None)
#        text = GROUP_ALL
#        btn = section.addButton(text, command=lambda: self.selectToolbarButton(text, False))
#        self.ToolbarButtonsDict[text] = (btn, None)        
        return toolbar
                
    def addRunButton(self, frame, text, col, imageFilename=None):
        btnImage = None
        if imageFilename:
            try:
                from protlib_filesystem import getXmippPath
                imgPath = os.path.join(getXmippPath('resources'), imageFilename)
                btnImage = tk.PhotoImage(file=imgPath)
            except tk.TclError:
                pass
        
        if btnImage:
            btn = tk.Button(frame, image=btnImage, bd=0, height=28, width=28)
            btn.image = btnImage
        else:
            btn = tk.Button(frame, text=text, font=Fonts['button'], bg=ButtonBgColor)
        btn.config(command=lambda:self.runButtonClick(text), 
                 activebackground=ButtonActiveBgColor)
        btn.grid(row=0, column=col)
        ToolTip(btn, text, 500)
        self.runButtonsDict[text] = btn
    
    
    def createHistoryFrame(self, parent):
        history = ProjectSection(parent, 'History')
        self.Frames['history'] = history
        
        history.addWidget(tk.Label, text="Filter")
        import ttk
        values = [GROUP_ALL]
        for k, v in sections:
            for o in v:
                values.append(o[0])
        self.cbDisplayGroup = history.addWidget(ttk.Combobox, values=values, state='readonly')
        self.cbDisplayGroup.bind('<<ComboboxSelected>>', self.cbDisplayGroupChanged)
        #cb.set(GROUP_ALL)
        
        aList = [(ACTION_EDIT, 'edit.gif', 'Edit    Alt-E/(Enter)'), 
                (ACTION_COPY, 'copy.gif', 'Duplicate   Alt-D/Ctrl-Enter'),
                (ACTION_REFRESH, 'refresh.gif', 'Refresh   F5'), 
                (ACTION_DELETE, 'delete.gif', 'Delete    Del')]
        def setupButton(k, v, t):
            btn =  history.addButton(k, v, command=lambda:self.runButtonClick(k), bg=HighlightBgColor)
            ToolTip(btn, t, 500)
            self.runButtonsDict[k] = btn
        for k, v, t in aList:
            setupButton(k, v, t)
        
        columns = ('State', 'Modified')
        tree = XmippTree(history.frameContent, columns=columns)
        for c in columns:
            tree.column(c, anchor='e')
            tree.heading(c, text=c) 
        tree.column('#0', width=300)
        tree.heading('#0', text='Run')
        tree.bind('<<TreeviewSelect>>', self.runSelectCallback)
        tree.bind('<Double-1>', lambda e:self.runButtonClick(ACTION_DEFAULT))
        tree.grid(row=0, column=0, sticky='nsew')
        history.frameContent.columnconfigure(0, weight=1)
        history.frameContent.rowconfigure(0, weight=1)
        self.lbHist = tree
        return history     
        
    def createDetailsFrame(self, parent):
        details = ProjectSection(parent, 'Details')
        self.Frames['details'] = details
        #Create RUN details
        details.addButton("Analyze results", command=self.visualizeRun, underline=0)
        details.addButton("Output files", command=self.showOutput, underline=0)
        content = details.frameContent
        content.config(bg=BgColor, bd=1, relief=tk.RIDGE)
        content.grid_configure(pady=(5, 0))
        
        self.detailsText = TaggedText(content, height=15, width=70)
        self.detailsText.frame.pack(fill=tk.BOTH)
        return details

    def createGUI(self, root=None):
        if not root:
            root = tk.Tk()
        self.root = root
        root.withdraw() # Hide the windows for centering
        projectName = os.path.basename(self.project.projectDir)
        hostName = getHostname()        
        self.root.title("Xmipp Protocols   Project: %(projectName)s  on  %(hostName)s" % locals())
        self.initVariables()        
        self.createMainMenu()

        #Create main frame that will contain all other sections
        #Configure min size and expanding behaviour
        root.minsize(750, 500)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main = tk.Frame(self.root)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, minsize=150)
        main.columnconfigure(1, minsize=450, weight=1)
        main.rowconfigure(1, minsize=200, weight=1)
        main.rowconfigure(2, minsize=200, weight=1)
        self.Frames['main'] = main
        
        registerCommonFonts()
        
        #Create section frames and locate them
        self.createToolbarFrame(main).grid(row=1, column=0, sticky='nse', padx=5, pady=5, rowspan=2)
        self.createHistoryFrame(main).grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self.createDetailsFrame(main).grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
        
        self.root.config(menu=self.menubar)
        #select lastSelected
        lastGroup = GROUP_ALL
        if self.project.config.has_option('project', 'lastselected'):
            lastGroup = self.project.config.get('project', 'lastselected')
            #self.selectToolbarButton(self.project.config.get('project', 'lastselected'), False)
        self.selectDisplayGroup(lastGroup)
        for k, v in self.ToolbarButtonsDict.iteritems():
            if lastGroup == v[0]:
                self.cbDisplayGroup.current(k)
                break
#        else:
#            self.Frames['details'].grid_remove()
    
        self.addBindings()
                
    def launchGUI(self, center=True):
        if center:
            centerWindows(self.root)
        self.root.deiconify()
        self.root.mainloop()
       
    def close(self, event=""):
        self.root.destroy()

    def showOutput(self, event=''):
        prot = self.project.getProtocolFromModule(self.lastRunSelected['script'])
        title = "Output Console - %s" % self.lastRunSelected['script']
        filelist = ["%s%s" % (prot.LogPrefix, ext) for ext in ['.log', '.out', '.err']]
        showTextfileViewer(title, filelist, self.root)
        
    def visualizeRun(self, event=''):
        run = self.getLastRunDict()
        self.launchProtocolGUI(run, True)

from protlib_xmipp import XmippScript

class ScriptProtocols(XmippScript):
    def __init__(self):
        XmippScript.__init__(self, True)
        
    def defineParams(self):
        self.addUsageLine("Create Xmipp project on this folder.");
        ## params
        self.addParamsLine("[ -c  ]            : Clean project");
        self.addParamsLine("   alias --clean;"); 
        
    def confirm(self, msg, default=True):
        centerWindows(self.root)
        result = askYesNo("NEW PROJECT", msg, self.root)
        return result
    
    def run(self):
        proj_dir = os.getcwd()
        project = XmippProject(proj_dir)
        self.root = tk.Tk()
        self.root.withdraw()
        launch = True
        if self.checkParam('--clean'):
            msg = 'You are in project: %s\n' % proj_dir
            msg += '<ALL RESULTS> will be <DELETED>, are you sure to <CLEAN>?'
            launch = self.confirm(msg, False)
            if launch:
                project.clean()
            else:
                print "CLEAN aborted."
                
        else: #lauch project     
            if not project.exists():    
                msg = 'You are in directory: <%s>\n' % proj_dir
                msg += 'Do you want to <CREATE> a <NEW PROJECT> in this folder?'
                launch = self.confirm(msg)
                if (launch):
                    project.create()
                else:
                    print "PROJECT CREATION aborted."
            else:
                project.load()
        if launch:
            gui = XmippProjectGUI(project)
            gui.createGUI(self.root)
            gui.launchGUI()

if __name__ == '__main__':
    ScriptProtocols().tryRun()
