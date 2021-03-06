# Copyright (C) 2003 - 2015 The Board of Regents of the University of Wisconsin System 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

""" This module implements the KeywordsTab class for the Data Window. """

__author__ = 'David Woods <dwoods@wcer.wisc.edu>, Nathaniel Case <nacase@wisc.edu>'

DEBUG = False
if DEBUG:
    print "KeywordsTab DEBUG is ON!!"

# Import wxPython
import wx

# import the Transana Clip Object
import Clip
# Import the Transana Collection Object
import Collection
# Import Transana's Dialogs
import Dialogs
# import Transana's Document Object
import Document
# Import the Transana Episode Object
import Episode
# Import the Keyword List Edit Form, for editing the Keyword List
import KeywordListEditForm
# import the Transana Quote Object
import Quote
# Import the Transana Library Object
import Library
# Import Transana's Constants
import TransanaConstants
# Import Transana's Exceptions
import TransanaExceptions
# Import Transana's Globals
import TransanaGlobal

# Import the Python string and sys modules
import string
import sys

# Define Menu Constants for the popup menu
MENU_KEYWORDSTAB_EDIT   = wx.NewId()
MENU_KEYWORDSTAB_DELETE = wx.NewId()

class KeywordsTab(wx.Panel):
    """Display associated keywords when an Episode or Clip is loaded."""

    def __init__(self, parent, seriesObj=None, episodeObj=None, documentObj=None, collectionObj=None, clipObj=None, quoteObj=None):
        """Initialize a KeywordsTab object."""
        # Let's remember our Parent
        self.parent = parent
        
        # Make the initial data objects which are passed in available to the entire KeywordsTab object
        self.seriesObj = seriesObj
        self.episodeObj = episodeObj
        self.documentObj = documentObj
        self.collectionObj = collectionObj
        self.clipObj = clipObj
        self.quoteObj = quoteObj

        # Get the size of the parent window
        psize = parent.GetSizeTuple()
        # Determine the size of the panel to be placed on the dialog, slightly smaller than the parent window
        width = psize[0] - 13 
        height = psize[1] - 45

        # Initialize a local pointer to the keyword list
        self.kwlist = None

        # Get the local keyword list pointer aimed at the appropriate source object.
        # NOTE:  If a Clip is defined use it (whether an episode is defined or not.)  If
        #        no clip is defined but an episode is defined, use that.
        if self.clipObj != None:
            self.kwlist = self.clipObj.keyword_list
        elif self.episodeObj != None:
            self.kwlist = self.episodeObj.keyword_list
        elif self.documentObj != None:
            self.kwlist = self.documentObj.keyword_list
        elif self.quoteObj != None:
            self.kwlist = self.quoteObj.keyword_list
            
        # Create a Panel to put stuff on.  Use WANTS_CHARS style so the panel doesn't eat the Enter key.
        # (This panel implements the Keyword Tab!  All of the window and Notebook structure is provided by DataWindow.py.)
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS, size=(width, height), name='KeywordsTabPanel')

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # Create a ListCtrl on the panel where the keyword data will be displayed
        self.lbKeywordsList = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        self.lbKeywordsList.InsertColumn(0, 'Keywords')
        mainSizer.Add(self.lbKeywordsList, 1, wx.EXPAND)

        # Update the display to show the keywords
        self.UpdateKeywords()

        # Create the Popup Menu.  It should have elements for Edit and Delete
        self.menu = wx.Menu()
        self.menu.Append(MENU_KEYWORDSTAB_EDIT, _("Edit"))
        wx.EVT_MENU(self, MENU_KEYWORDSTAB_EDIT, self.OnEdit)
        self.menu.Append(MENU_KEYWORDSTAB_DELETE, _("Delete"))
        wx.EVT_MENU(self, MENU_KEYWORDSTAB_DELETE, self.OnDelete)

        # Define the Key Down Event Handler
        self.lbKeywordsList.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        # Define the Right-Click event (which calls the popup menu)
        wx.EVT_RIGHT_DOWN(self.lbKeywordsList, self.OnRightDown)

        # Perform GUI Layout
        self.SetSizer(mainSizer)
        self.SetAutoLayout(True)
        self.Layout()

    def Refresh(self):
        """ This method allows up to update all data when this tab is displayed.  This is necessary as the objects may have
            been changed since they were originally loaded.  """

        try:
            # If a Library Object is defined, reload it
            if self.seriesObj != None:
                self.seriesObj = Library.Library(self.seriesObj.number)
            # If an Episode Object is defined, reload it
            if self.episodeObj != None:
                self.episodeObj = Episode.Episode(self.episodeObj.number)
            # if a Documetn Object is defined, reload it
            if self.documentObj != None:
                self.documentObj = Document.Document(self.documentObj.number)
            # If a Collection Object is defined, reload it
            if self.collectionObj != None:
                self.collectionObj = Collection.Collection(self.collectionObj.number)
            # If a Clip Object is defined, reload it.
            if self.clipObj != None:
                self.clipObj = Clip.Clip(self.clipObj.number)
            # If a Quote Object is defined, reload it.
            if self.quoteObj != None:
                self.quoteObj = Quote.Quote(self.quoteObj.number)
            # Get the local keyword list pointer aimed at the appropriate source object.
            # NOTE:  If a Clip is defined use it (whether an episode is defined or not.)  If
            #        no clip is defined but an episode is defined, use that.
            if self.clipObj != None:
                self.kwlist = self.clipObj.keyword_list
            elif self.episodeObj != None:
                self.kwlist = self.episodeObj.keyword_list
            elif self.documentObj != None:
                self.kwlist = self.documentObj.keyword_list
            elif self.quoteObj != None:
                self.kwlist = self.quoteObj.keyword_list

            # Update the Tab Display
            self.UpdateKeywords()
        except TransanaExceptions.RecordNotFoundError:
            msg = _("The appropriate Keyword data could not be loaded from the database.")
            if not TransanaConstants.singleUserVersion:
                msg += '\n' + _("This data may have been deleted by another user.")
            tmpDlg = Dialogs.ErrorDialog(self.parent, msg)
            tmpDlg.ShowModal()
            tmpDlg.Destroy()
            # Return to the database tab
            self.parent.parent.ControlObject.ShowDataTab(0)


    def UpdateKeywords(self, sendMUMessage=False):
        """ Update the display to display all keywords in the Keyword List """
        # Clear the visible control
        self.lbKeywordsList.DeleteAllItems()

        # Display header information
        self.lbKeywordsList.InsertStringItem(0, _('Keywords for:'))

        if self.seriesObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Library: "%s"'), 'utf8')
            else:
                prompt = _('Library: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.seriesObj.id)
            
        if self.episodeObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Episode: "%s"'), 'utf8')
            else:
                prompt = _('Episode: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.episodeObj.id)

        if self.documentObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Document: "%s"'), 'utf8')
            else:
                prompt = _('Document: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.documentObj.id)

        if self.collectionObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Collection: "%s"'), 'utf8')
            else:
                prompt = _('Collection: "%s"')
            # We want to show the full collection path, but it gets pretty wide pretty quickly, so let's do it
            # on multiple lines.  First, let's get the individual Collection nodes
            collNodes = self.collectionObj.GetNodeData()
            # Put the first node out with the Collection prompt
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % collNodes[0])
            # Iterate through rest of the nodes, skipping the first ...
            for node in collNodes[1:]:
                # ... and add them to the ListCtrl
                self.lbKeywordsList.InsertStringItem(sys.maxint, '    > "%s"' % node)

        if self.clipObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Clip: "%s"'), 'utf8')
            else:
                prompt = _('Clip: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.clipObj.id)
            # Update the Keyword Visualization, as the clip's keywords have probably changed.
            self.parent.parent.ControlObject.UpdateKeywordVisualization()
            # Even if this computer doesn't need to update the keyword visualization others, might need to.
            if not TransanaConstants.singleUserVersion and sendMUMessage:
                # We need to update the Keyword Visualization for the current ClipObject
                if DEBUG:
                    print 'Message to send = "UKV %s %s %s"' % ('Clip', self.clipObj.number, self.clipObj.episode_num)
                    
                if TransanaGlobal.chatWindow != None:
                    TransanaGlobal.chatWindow.SendMessage("UKV %s %s %s" % ('Clip', self.clipObj.number, self.clipObj.episode_num))

        if self.quoteObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Quote: "%s"'), 'utf8')
            else:
                prompt = _('Quote: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.quoteObj.id)
            # Update the Keyword Visualization, as the quote's keywords have probably changed.
            self.parent.parent.ControlObject.UpdateKeywordVisualization()
            # Even if this computer doesn't need to update the keyword visualization others, might need to.
            if not TransanaConstants.singleUserVersion and sendMUMessage:
                # We need to update the Keyword Visualization for the current QuoteObject
                if DEBUG:
                    print 'Message to send = "UKV %s %s %s"' % ('Quote', self.quoteObj.number, self.quoteObj.source_document_num)
                    
                if TransanaGlobal.chatWindow != None:
                    TransanaGlobal.chatWindow.SendMessage("UKV %s %s %s" % ('Quote', self.quoteObj.number, self.quoteObj.source_document_num))

        self.lbKeywordsList.InsertStringItem(sys.maxint, '')

        # Add the keywords from the list to the display
        for kws in self.kwlist:
            self.lbKeywordsList.InsertStringItem(sys.maxint, kws.keywordPair)
        # Set the column size to match the control width
        (width, height) = self.lbKeywordsList.GetSizeTuple()
        self.lbKeywordsList.SetColumnWidth(0, width)

    def OnKeyDown(self, event):
        """ Handle Key Down Events """
        # See if the ControlObject wants to handle the key that was pressed.
        if self.parent.parent.ControlObject.ProcessCommonKeyCommands(event):
            # If so, we're done.  (Actually, we're done anyway.)
            return

    def OnRightDown(self, event):
        """ Right-click event --> Show popup menu """
        # Determine the item that has been right-clicked.  -1 indicates the click was not on an item.
        (x, y) = event.GetPosition()
        (idVal, flags) = self.lbKeywordsList.HitTest(wx.Point(x, y))
        # If a keyword (rather than a header line) is selected, enable the Delete option
        if idVal > 3:
            # Select the item that was clicked
            self.lbKeywordsList.SetItemState(idVal, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            # Enable the Delete menu item
            self.menu.Enable(MENU_KEYWORDSTAB_DELETE, True)
        # ... else if no non-header item was the click target ...
        else:
            # loop through all the items in the listCtrl ...
            for loop in range(self.lbKeywordsList.GetItemCount()):
                # print loop, self.lbKeywordsList.GetItemText(loop), self.lbKeywordsList.GetItemState(loop, wx.LIST_STATE_SELECTED)
                # ... and if one is selected ...
                if self.lbKeywordsList.GetItemState(loop, wx.LIST_STATE_SELECTED) > 0:
                    # ... de-select it.
                    self.lbKeywordsList.SetItemState(idVal, 0, wx.LIST_STATE_SELECTED)
            # and disable the Delete menu item
            self.menu.Enable(MENU_KEYWORDSTAB_DELETE, False)
            
        # Pop up the popup menu
        self.PopupMenu(self.menu, event.GetPosition())

    def OnEdit(self, event):
        """ Selecting 'Edit' from the popup menu takes you to the Keyword List Edit Form """
        # Lock the appropriate record
        # NOTE:  If a Clip is defined use it (whether an episode is defined or not.)  If
        #        no clip is defined but an episode is defined, use that.
        if self.clipObj != None:
            obj = self.clipObj
        elif self.episodeObj != None:
            obj = self.episodeObj
        elif self.documentObj != None:
            obj = self.documentObj
        elif self.quoteObj != None:
            obj = self.quoteObj
            
        try:
            obj.lock_record()
            # Create/define the Keyword List Edit Form
            dlg = KeywordListEditForm.KeywordListEditForm(self.parent.parent, -1, _("Edit Keyword List"), obj, self.kwlist)
            # Set the "continue" flag to True (used to redisplay the dialog if an exception is raised)
            contin = True
            # While the "continue" flag is True ...
            while contin:
                # if the user pressed "OK" ...
                try:
                    # Show the Keyword List Edit Form and process it if the user selects OK
                    if dlg.ShowModal() == wx.ID_OK:
                        # Clear the local keywords list and repopulate it from the Keyword List Edit Form
                        self.kwlist = []
                        for kw in dlg.keywords:
                            self.kwlist.append(kw)

                        # Copy the local keywords list into the appropriate object and save that object
                        obj.keyword_list = self.kwlist

                        if isinstance(obj, Clip.Clip):
                            for (keywordGroup, keyword, clipNum) in dlg.keywordExamplesToDelete:
                                # Load the specified Clip record.  Save time by skipping the Clip Transcript, which we don't need.
                                tempClip = Clip.Clip(clipNum, skipText=True)
                                # Prepare the Node List for removing the Keyword Example Node
                                nodeList = (_('Keywords'), keywordGroup, keyword, tempClip.id)
                                # Call the DB Tree's delete_Node method.  Include the Clip Record Number so the correct Clip entry will be removed.
                                self.parent.GetPage(0).tree.delete_Node(nodeList, 'KeywordExampleNode', tempClip.number)

                        # If we are dealing with an Episode ...
                        if isinstance(obj, Episode.Episode):
                            # Check to see if there are keywords to be propagated
                            self.parent.parent.ControlObject.PropagateObjectKeywords(_('Episode'), obj.number, obj.keyword_list)
                        # If we're dealing with a Document ...
                        elif isinstance(obj, Document.Document):
                            # Check to see if there are keywords to be propagated
                            self.parent.parent.ControlObject.PropagateObjectKeywords(_('Document'), obj.number, obj.keyword_list)
                        obj.db_save()

                        # Now let's communicate with other Transana instances if we're in Multi-user mode
                        if not TransanaConstants.singleUserVersion:
                            if isinstance(obj, Episode.Episode):
                                msg = 'Episode %d' % obj.number
                            elif isinstance(obj, Clip.Clip):
                                msg = 'Clip %d' % obj.number
                            elif isinstance(obj, Document.Document):
                                msg = 'Document %d' % obj.number
                            elif isinstance(obj, Quote.Quote):
                                msg = 'Quote %d' % obj.number

                                print "KeywordsTab.OnEdit():  UKL sent for %s!!" % msg
                                
                            else:
                                msg = ''
                            if msg != '':
                                if DEBUG:
                                    print 'Message to send = "UKL %s"' % msg
                                if TransanaGlobal.chatWindow != None:
                                    # Send the "Update Keyword List" message
                                    TransanaGlobal.chatWindow.SendMessage("UKL %s" % msg)

                        # Update the display to reflect changes in the Keyword List
                        self.UpdateKeywords(sendMUMessage=True)
                        # If we do all this, we don't need to continue any more.
                        contin = False
                    # If the user pressed Cancel ...
                    else:
                        # ... then we don't need to continue any more.
                        contin = False
                # Handle "SaveError" exception
                except TransanaExceptions.SaveError:
                    # Display the Error Message, allow "continue" flag to remain true
                    errordlg = Dialogs.ErrorDialog(None, sys.exc_info()[1].reason)
                    errordlg.ShowModal()
                    errordlg.Destroy()
                    # Refresh the Keyword List, if it's a changed Keyword error
                    dlg.refresh_keywords()
                    # Highlight the first non-existent keyword in the Keywords control
                    dlg.highlight_bad_keyword()

                # Handle other exceptions
                except:
                    if DEBUG:
                        import traceback
                        traceback.print_exc(file=sys.stdout)
                    # Display the Exception Message, allow "continue" flag to remain true
                    if 'unicode' in wx.PlatformInfo:
                        # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                        prompt = unicode(_("Exception %s: %s"), 'utf8')
                    else:
                        prompt = _("Exception %s: %s")
                    errordlg = Dialogs.ErrorDialog(None, prompt % (sys.exc_info()[0], sys.exc_info()[1]))
                    errordlg.ShowModal()
                    errordlg.Destroy()

            # Unlock the appropriate record
            obj.unlock_record()
            # Free the memory used for the Keyword List Edit Form  
            dlg.Destroy()
        except TransanaExceptions.RecordLockedError, e:
            self.handleRecordLock(e)
        # Process TypeError exception, which probably indicates that the underlying object has been deleted.
        except TypeError, e:
            if self.clipObj != None:
                tempObjType = _('Clip')
            elif self.episodeObj != None:
                tempObjType = _('Episode')
            elif self.documentObj != None:
                tempObjType = _('Document')
            elif self.quoteObj != None:
                tempObjType = _('Quote')
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                msg = unicode(_('You cannot proceed because %s "%s" cannot be found.'), 'utf8') + \
                      unicode(_('\nIt may have been deleted by another user.'), 'utf8')
                msg = msg % (unicode(tempObjType, 'utf8'), obj.id)
            else:
                msg = _('You cannot proceed because %s "%s" cannot be found.') + \
                      _('\nIt may have been deleted by another user.') % (tempObjType, obj.id)
            dlg = Dialogs.ErrorDialog(self.parent, msg)
            dlg.ShowModal()
            dlg.Destroy()
            # Clear the deleted objects from the Transana Interface.  Otherwise, problems arise.
            wx.CallAfter(self.parent.parent.ControlObject.ClearAllWindows)

    def OnDelete(self, event):
        """ Selecting 'Delete' from the popup menu deletes a keyword """
        # Delete the appropriate keyword
        # NOTE:  Because self.kwlist is just a pointer to the keyword list in the appropriate object,
        #        removing the keyword from the object also removes it from the local kwlist!

        # Let's iterate through the ListCtrl FROM THE BOTTOM UP (since as items get deleted, the list gets shorter!) ...
        for selItem in range(self.lbKeywordsList.GetItemCount() - 1, -1, -1):
            # ... looking for an item that is selected ...
            if self.lbKeywordsList.GetItemState(selItem, wx.LIST_STATE_SELECTED) > 0:
                # ... separate out the Keyword Group and the Keyword
                kwlist = string.split(self.lbKeywordsList.GetItemText(selItem), ':')
                kwg = string.strip(kwlist[0])
                kw = ':'.join(kwlist[1:]).strip()

                try:
                    # Initialize the MU Chat Message
                    msg = ''
                    # NOTE:  If a Clip is defined use it (whether an episode is defined or not.)  If
                    #        no clip is defined but an episode is defined, use that.
                    if self.clipObj != None:
                        # Lock the record
                        self.clipObj.lock_record()
                        # Remove the keyword from the object
                        delResult = self.clipObj.remove_keyword(kwg, kw)
                        if delResult != 0:
                            # Save the object
                            self.clipObj.db_save()
                            # If we are deleting a Keyword Example, we need to removed the node from the Database Tree Tab
                            if delResult == 2:
                                nodeList = (_('Keywords'), kwg, kw, self.clipObj.id)
                                self.parent.GetPage(0).tree.delete_Node(nodeList, 'KeywordExampleNode', self.clipObj.number)
                            # Define the MU Chat Message
                            msg = 'Clip %d' % self.clipObj.number

                        # Unlock the record
                        self.clipObj.unlock_record()
                    elif self.episodeObj != None:
                        # Lock the record
                        self.episodeObj.lock_record()
                        # Remove the keyword from the object
                        delResult = self.episodeObj.remove_keyword(kwg, kw)
                        # Save the object
                        self.episodeObj.db_save()
                        # Define the MU Chat Message
                        msg = 'Episode %d' % self.episodeObj.number
                        # Unlock the record
                        self.episodeObj.unlock_record()

                    elif self.quoteObj != None:
                        # Lock the record
                        self.quoteObj.lock_record()
                        # Remove the keyword from the object
                        delResult = self.quoteObj.remove_keyword(kwg, kw)
                        # Save the object
                        self.quoteObj.db_save()
                        # Define the MU Chat Message
                        msg = 'Quote %d' % self.quoteObj.number
                        # Unlock the record
                        self.quoteObj.unlock_record()
                        # I'm not sure why Quotes are different, but we need to update the Keyword List here
                        # when we don't for any other object type.
                        self.kwlist = self.quoteObj.keyword_list

                    elif self.documentObj != None:
                        # Lock the record
                        self.documentObj.lock_record()
                        # Remove the keyword from the object
                        delResult = self.documentObj.remove_keyword(kwg, kw)
                        # Save the object
                        self.documentObj.db_save()
                        # Define the MU Chat Message
                        msg = 'Document %d' % self.documentObj.number
                        # Unlock the record
                        self.documentObj.unlock_record()
                        
                        print "KeywordsTab.OnDelete():  UKL sent for %s!!" % msg

                    # If there's an MU Chat Message ...
                    if (not TransanaConstants.singleUserVersion) and (msg != ''):
                        if DEBUG:
                            print 'Message to send = "UKL %s"' % msg
                        # ... and there's a chat window ...
                        if TransanaGlobal.chatWindow != None:
                            # ... then send the "Update Keyword List" message
                            TransanaGlobal.chatWindow.SendMessage("UKL %s" % msg)
                            
                except TransanaExceptions.RecordLockedError, e:
                    self.handleRecordLock(e)
                # Process TypeError exception, which probably indicates that the underlying object has been deleted.
                except TypeError, e:
                    if self.clipObj != None:
                        obj = self.clipObj
                        tempObjType = _('Clip')
                    elif self.episodeObj != None:
                        obj = self.episodeObj
                        tempObjType = _('Episode')
                    elif self.documentObj != None:
                        obj = self.documentObj
                        tempObjType = _('Document')
                    elif self.quoteObj != None:
                        obj = self.quoteObj
                        tempObjType = _('Quote')
                    if 'unicode' in wx.PlatformInfo:
                        # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                        msg = unicode(_('You cannot proceed because %s "%s" cannot be found.'), 'utf8') + \
                              unicode(_('\nIt may have been deleted by another user.'), 'utf8')
                        msg = msg % (unicode(tempObjType, 'utf8'), obj.id)
                    else:
                        msg = _('You cannot proceed because %s "%s" cannot be found.') + \
                              _('\nIt may have been deleted by another user.') % (tempObjType, obj.id)
                    dlg = Dialogs.ErrorDialog(self.parent, msg)
                    dlg.ShowModal()
                    dlg.Destroy()
                    # Clear the deleted objects from the Transana Interface.  Otherwise, problems arise.
                    wx.CallAfter(self.parent.parent.ControlObject.ClearAllWindows)
        # Update the display to reflect changes in the Keyword List
        self.Refresh()

    def handleRecordLock(self, e):
        """ Handles Record Lock exceptions """
        # Determine if the lock is caused by the local user
        if e.user != TransanaGlobal.userName:
            # If not, produce the standard Record Lock error message.
            # If we're working with a Clip Object ...
            if self.clipObj != None:
                # ... determine the appropriate Clip error message data
                rtype = _("Clip")
                idVal = self.clipObj.id
            # If we're working with an Episode Object ...
            elif self.episodeObj != None:
                # ... determine the appropriate Episode error message data
                rtype = _("Episode")
                idVal = self.episodeObj.id
            # If we're working with a Document Object ...
            elif self.documentObj != None:
                # ... determine the appropriate Document error message data
                rtype = _("Document")
                idVal = self.documentObj.id
            # If we're working with a Quote Object ...
            elif self.quoteObj != None:
                # ... determine the appropriate Quote error message data
                rtype = _("Quote")
                idVal = self.quoteObj.id
            TransanaExceptions.ReportRecordLockedException(rtype, idVal, e)
        # If the lock IS caused by the local user ...
        else:
            # Well, actually it COULD be another user on the same user account.  Let's check.
            # Initialize counter for users with this user name
            userCount = 0
            # Iterate through the list of users ...
            for x in range(TransanaGlobal.chatWindow.userList.GetCount()):
                # ... and if the current user name matches the entry in the list of users ...
                if TransanaGlobal.userName == TransanaGlobal.chatWindow.userList.GetString(x)[:len(TransanaGlobal.userName)]:
                    # ... increment the counter.  (NOTE:  "BobJones" will be counted when looking for "Bob".  Oh well.)
                    userCount += 1
            # Create an error message that covers the most likely problem.
            msg = _('You have the transcript open for editing.  You need to leave edit mode to unlock %s "%s"\nto be able to edit the %s keywords.')
            # If there are multiple users with the same account name ...
            if userCount > 1:
                # ... then add the contingency error message
                msg += _("\n(If there is another person using the same user account, they might have the record locked.)")
            # If we're working with a Clip Object ...
            if self.clipObj != None:
                # ... determine the appropriate Clip error message data
                rtype = _("Clip")
                idVal = self.clipObj.id
            # If we're working with an Episode Object ...
            elif self.episodeObj != None:
                # ... determine the appropriate Episode error message data
                rtype = _("Episode")
                idVal = self.episodeObj.id
            # If we're working with a Document Object ...
            elif self.documentObj != None:
                # ... determine the appropriate Document error message data
                rtype = _("Document")
                idVal = self.documentObj.id
            # If we're working with a Quote Object ...
            elif self.quoteObj != None:
                # ... determine the appropriate Quote error message data
                rtype = _("Quote")
                idVal = self.quoteObj.id
            # Convert the error message and error message data to Unicode if necessary
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                msg = unicode(msg, 'utf8')
                if isinstance(rtype, str):
                    rtype = unicode(rtype, 'utf8')
                if isinstance(idVal, str):
                    idVal = unicode(idVal, 'utf8')
            # Set up the Data Structure that matches the Error Message created above.
            data = (rtype, idVal, rtype)

            # Display the error message that was created above            
            dlg = Dialogs.ErrorDialog(self.parent, msg % data)
            dlg.ShowModal()
            dlg.Destroy()
