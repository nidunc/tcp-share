from cgitb import text
from sre_parse import State
from modules.app.helper import Vector2

from modules.gui.gui_module import GuiModule

from tkinter import *
from tkinter.font import BOLD

import subprocess
from pathlib import Path

from modules.tcp import TCP
from modules.translate import Translate

class GUI_ShareFiles( GuiModule ):

    def openSendChoiceModal( self, server : TCP.Server_t ) -> None:
        # Create a new Toplevel window (modal)
        modal = Toplevel( self.gui )
        modal.title( f"Keuze" )
        modal.grab_set()

        Label(modal, text=f"Tekstbestanden of PDF's versturen naar \n {server['ip']}:{server['port']}?").pack( pady=10 )

        button_state = NORMAL if self.context.read_write.hasTextFiles() else DISABLED
        Button( modal, text="Tekst", state=button_state, command=lambda: 
               self.sendChoiceModalCallback( server, modal, "Tekst" ) ).pack( side=LEFT, padx=20, pady=20 )


        button_state = NORMAL if self.context.read_write.hasPdfFiles() else DISABLED
        Button( modal, text="PDF", state=button_state, 
               command=lambda: self.sendChoiceModalCallback( server, modal, "PDF" ) ).pack( side=RIGHT, padx=20, pady=20 )

    def sendChoiceModalCallback( self, server : TCP.Server_t, modal, choice ):
        if choice == "PDF":
            print( f"Create and send pdf! {server}")
            self.send_pdf_file( server )
        else:
            print( f"Send txt! {server}")
            self.send_txt_files( server )

        modal.destroy()

    def send_txt_files( self, server : TCP.Server_t ):
        print(f"Attempt to share files to: {server}")
        
        if not self.context.tcp.server_clear_files( server ):
            print("server did not allow to clear text files")
            return

        files = self.context.read_write.getTransferFiles()
        print(files)

        for file in files:
            self.context.tcp.client_send_file( server, file['filename'], file['contents'].decode() )

    def send_pdf_file( self, server : TCP.Server_t ):
        files = self.context.read_write.getPdfFiles()
        
        print(f"Attempt to share PDF files to: {server}")

        for file in files:
            self.context.tcp.client_send_file( server, file['filename'], file['contents'] )

    def updateDevice( self, device ):
        is_online = True if self.context.tcp.ping_device( device['ip'] ) else False
        is_allowing = False

        device['gui']['send'].config( state=DISABLED )

        if is_online:
            server : TCP.Server_t = { 'ip' : device['ip'], 'port' : self.settings.tcp_port }
            is_allowing = self.context.tcp.get_allow_receive( server ) 

            if is_allowing:
                device['gui']['status'].config( text="Ready")
                device['gui']['status_indicator'].config( bg="#00ff00" )
                device['gui']['send'].config( state=NORMAL )
            else:
                device['gui']['status'].config( text="Refusing")
                device['gui']['status_indicator'].config( bg="#fc8c03" )
        else:
            device['gui']['status'].config( text="Offline")
            device['gui']['status_indicator'].config( bg="#ff0000" )

        print( f"Device {device['hostname']} on IP {device['ip']} online: {is_online} allowing: {is_allowing}" )

    def updateDevices( self ):
        for device in self.settings.LAN_devices:
            self.updateDevice( device )

    def drawDevice( self, device, content_frame ):   
        device['gui'] = {}
        device['gui']['frame'] = Frame( content_frame, bg="white", padx=10, pady=5 )
        device['gui']['frame'].pack( side=TOP, fill='both' ) 
        frame = device['gui']['frame']

        # setting size on 'frame' doesnt work?
        pseudo_element = Frame( frame, width = (self.settings.appplication_width - 40 ), height = 45)
        pseudo_element.pack( side=LEFT, fill='x' )

        device['gui']['status_indicator'] = Frame( frame, bg="#d1d1d1", padx=0, pady=0 )
        device['gui']['status_indicator'].place( x=-0, y=-0, width=3, heigh =45 ) 

        pos_x = 10

        server : TCP.Server_t = { 'ip': device['ip'], 'port': self.settings.tcp_port }

        device['gui']['send'] = Button( frame, text = device['hostname'], state=DISABLED,
                command = lambda param=server: self.openSendChoiceModal(param) )
        device['gui']['send'].place( y=10, x=pos_x )

        device['gui']['status'] = Label( frame, text=f"-")
        device['gui']['status'].place( x = 300, y = 10 ) 

        self.current_position.y += 55

    def on_frame_configure(self, event):
        # Update the scrollregion of the canvas whenever the content frame's size changes
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def drawDevices( self ):
        # frame
        frame = Frame( self )
        frame.place(  y = self.current_position.y,
                      width=self.settings.appplication_width, 
                      height=self.settings.appplication_height - 225 )

        # canvas
        self.canvas = Canvas( frame, bg='white' )
        self.canvas.pack( side=LEFT, fill='both', expand=True )

        # scrollbar
        y_scrollbar = Scrollbar( frame, orient=VERTICAL, command=self.canvas.yview )
        y_scrollbar.pack( side=RIGHT, fill=Y )
        self.canvas.configure(yscrollcommand=y_scrollbar.set)

        # canvas, again
        content_frame = Frame( self.canvas )

        for device in self.settings.LAN_devices:
            self.drawDevice( device, content_frame )

        # update region of canvas
        self.canvas.create_window((0, 0), window=content_frame, anchor='nw')
        content_frame.update_idletasks()
        self.canvas.config( scrollregion=self.canvas.bbox( "all" ) )
        content_frame.bind( "<Configure>", self.on_frame_configure )

    def allowConnectionCheckboxCallback( self ):
        self.settings.allowConnection = self.allowCon.get()

    def goToViewFiles( self ):
        reload_frame : bool = True # redundant bool ..
        self.gui.show_frame( self.gui.FRAME_VIEW_FILES, reload_frame )

    def openPDFFolderInExplorer( self ):
        print( f"open pdf folder: {self.context.read_write.pdfDir}" )

        folder_path = self.context.read_write.pdfDir

        folder_path.mkdir(parents=True, exist_ok=True)

        subprocess.run(['explorer', folder_path])

    def create_pdf( self ):
        self.context.to_pdf.txt_to_pdf()
        print("create pdf")

    def drawActionButtons( self ) -> None:
        # browse txt files
        browse_txt = Button( self, text = "browse txt", 
               command = lambda : self.goToViewFiles() )
        browse_txt.place( x = (self.settings.appplication_width / 2 ) - 125, 
                      y = self.current_position.y )


        # translate button
        refresh = Button( self, text = "Translate", 
               command = lambda : self.context.translate.openTranslateModal() )
        refresh.place( x = (self.settings.appplication_width / 2 ) - 45, y = self.current_position.y )

        # If PDF files exist, draw browse button
        # Otherwise draw the create button
        #
        # Note: It is allowed to create variable 'browse_pdf' 
        # in the scope of the if else block and use it afterwards in python
        # it seems ..
        if self.context.read_write.hasPdfFiles():
            browse_pdf = Button( self, text = "browse pdf", 
                   command = lambda : self.openPDFFolderInExplorer() )
        else:
            browse_pdf = Button( self, text = "create pdf", 
                   command = lambda : self.create_pdf() )

        browse_pdf.place( x = (self.settings.appplication_width / 2 ) + 25, 
                          y = self.current_position.y )        
        
        self.current_position.y += 25

    def drawEncryptedIndicator(self) -> None:
        """
        Draw a label that indicates whether the files are encrypted or not.
        The border is defined with a Frame, and the Label is placed within the Frame.
        """
        status = "Er waren geen tekstbestanden gevonden!"
        fg_colour = "whitesmoke"
        bg_colour = "lightgrey"

        if self.context.read_write.hasAnyTextFiles():
            if self.context.read_write.hasPasswordsFile():
                status = "De tekstbestanden zijn versleuteld!"
                fg_colour = "palegreen"
                bg_colour = "lightgreen"
            else:
                status = "De tekstbestanden zijn niet versleuteld!"
                fg_colour = "lightpink"
                bg_colour = "lightcoral"

        border = Frame(self, background=bg_colour, borderwidth=2)

        indicator = Label(
            border, text=status, fg="black", bg=fg_colour, font=("Helvetica", 14, "bold")
        )

        indicator.pack()
        border.pack()

    def _debugClearFiles( self ) -> None:
        """Debug function to clear all files 'txt' and 'pdf'"""
        self.context.read_write.removeTransferFiles()
        self.context.read_write.removePdfFiles()
        self.context.read_write.removeQRFiles()

    def openLogs( self ):
        reload_frame : bool = True # redundant bool ..
        self.gui.show_frame( self.gui.FRAME_VIEW_LOGS, reload_frame )

    def onStart( self ):
        lan_info = Label( self, text=f"LAN Address: {self.settings.server_ip}:{self.settings.tcp_port}" )
        lan_info.configure(font=("Helvetica", 14, "bold"))
        lan_info.pack()

        header = Label( self, text=f"Aantal bestanden gevonden: {self.context.read_write.numShareableFiles}")
        header.pack()
            
        language : Translate.Language_t = self.context.translate.getCurrentLanguage()
        lang = Label( self, text=f"Taal: {language['name']}")
        lang.pack()

        self.device_frame = {}
        self.current_position = Vector2( 0, 80 )
        
        self.drawEncryptedIndicator()
        
        self.current_position = Vector2( 0, 110 )

        self.drawActionButtons()

        self.allowCon = IntVar( value=self.settings.allowConnection )
        c1 = Checkbutton( self, text='Verbindingen Toestaan',variable=self.allowCon, onvalue=1, offvalue=0, 
                        command=lambda : self.allowConnectionCheckboxCallback() )
        c1.place( x = 15, y =  self.current_position.y )

        self.current_position.y += 30

        # draw LAN devices
        self.drawDevices()

        # force LAN device status refresh
        refresh = Button( self, text = "Lijst vernieuwen", 
               command = lambda : self.context.bg_worker_force_gui_update() )
        refresh.place( x = 10, 
                      y = self.settings.appplication_height - 40 )

        # debug button to create QR codes
        create_qr = Button( self, text = "Create QR", 
               command = lambda : self.context.qrcode.create_qr_codes() )
        create_qr.place( x = 120, 
                      y = self.settings.appplication_height - 40 )

        # force a gui pass in bg_worker to ping LAN devices
        self.context.bg_worker_force_gui_update()

        logs = Button( self, text = "Logs", 
               command = lambda : self.openLogs() )
        logs.place( x = self.settings.appplication_width - 180, 
                      y = self.settings.appplication_height - 40 )

        button = Button( self, text = "Opnieuw Beginnen", 
               command = lambda : self._debugClearFiles() )
        button.place( x = self.settings.appplication_width - 130, 
                      y = self.settings.appplication_height - 40 )

