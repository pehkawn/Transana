# Copyright (C) 2003 - 2006 The Board of Regents of the University of Wisconsin System 
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

# Import wxPython
import wx

# import the Transana Clip Object
import Clip
# Import the Transana Collection Object
import Collection
# Import the Transana Episode Object
import Episode
# Import the Keyword List Edit Form, for editing the Keyword List
import KeywordListEditForm
# Import the Transana Series Object
import Series

# Import the Python string and sys modules
import string
import sys

# Define Menu Constants for the popup menu
MENU_KEYWORDSTAB_EDIT   = wx.NewId()
MENU_KEYWORDSTAB_DELETE = wx.NewId()

class KeywordsTab(wx.Panel):
    """Display associated keywords when an Episode or Clip is loaded."""

    def __init__(self, parent, seriesObj=None, episodeObj=None, collectionObj=None, clipObj=None):
        """Initialize a KeywordsTab object."""
        # Let's remember our Parent
        self.parent = parent
        
        # Make the initial data objects which are passed in available to the entire KeywordsTab object
        self.seriesObj = seriesObj
        self.episodeObj = episodeObj
        self.collectionObj = collectionObj
        self.clipObj = clipObj

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
            
        # Create a Panel to put stuff on.  Use WANTS_CHARS style so the panel doesn't eat the Enter key.
        # (This panel implements the Keyword Tab!  All of the window and Notebook structure is provided by DataWindow.py.)
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS, size=(width, height), name='KeywordsTabPanel')

        # Create a ListCtrl on the panel where the keyword data will be displayed
        lay = wx.LayoutConstraints()
        lay.left.SameAs(self, wx.Left, 1)
        lay.top.SameAs(self, wx.Top, 1)
        lay.right.SameAs(self, wx.Right, 1)
        lay.bottom.SameAs(self, wx.Bottom, 1)
        self.lbKeywordsList = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.lbKeywordsList.InsertColumn(0, 'Keywords')
        self.lbKeywordsList.SetConstraints(lay)

        # Update the display to show the keywords
        self.UpdateKeywords()

        # Create the Popup Menu.  It should have elements for Edit and Delete
        self.menu = wx.Menu()
        self.menu.Append(MENU_KEYWORDSTAB_EDIT, _("Edit"))
        wx.EVT_MENU(self, MENU_KEYWORDSTAB_EDIT, self.OnEdit)
        self.menu.Append(MENU_KEYWORDSTAB_DELETE, _("Delete"))
        wx.EVT_MENU(self, MENU_KEYWORDSTAB_DELETE, self.OnDelete)

        # Define the Right-Click event (which calls the popup menu)
        wx.EVT_RIGHT_DOWN(self.lbKeywordsList, self.OnRightDown)

        # Perform GUI Layout
        self.Layout()
        self.SetAutoLayout(True)

    def Refresh(self):
        """ This method allows up to update all data when this tab is displayed.  This is necessary as the objects may have
            been changed since they were originally loaded.  """

        # If a Series Object is defined, reload it
        if self.seriesObj != None:
            self.seriesObj = Series.Series(self.seriesObj.number)
        # If an Episode Object is defined, reload it
        if self.episodeObj != None:
            self.episodeObj = Episode.Episode(self.episodeObj.number)
        # If a Collection Object is defined, reload it
        if self.collectionObj != None:
            self.collectionObj = Collection.Collection(self.collectionObj.number)
        # If a Clip Object is defined, reload it
        if self.clipObj != None:
            self.clipObj = Clip.Clip(self.clipObj.number)

        # Get the local keyword list pointer aimed at the appropriate source object.
        # NOTE:  If a Clip is defined use it (whether an episode is defined or not.)  If
        #        no clip is defined but an episode is defined, use that.
        if self.clipObj != None:
            self.kwlist = self.clipObj.keyword_list
        elif self.episodeObj != None:
            self.kwlist = self.episodeObj.keyword_list

        # Update the Tab Display
        self.UpdateKeywords()


    def UpdateKeywords(self):
        """ Update the display to display all keywords in the Keyword List """
        # Clear the visible control
        self.lbKeywordsList.DeleteAllItems()

        # Display header information
        self.lbKeywordsList.InsertStringItem(0, _('Keywords for:'))

        if self.seriesObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Series: "%s"'), 'utf8')
            else:
                prompt = _('Series: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.seriesObj.id)
            
        if self.episodeObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Episode: "%s"'), 'utf8')
            else:
                prompt = _('Episode: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.episodeObj.id)

        if self.collectionObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Collection: "%s"'), 'utf8')
            else:
                prompt = _('Collection: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.collectionObj.id)

        if self.clipObj != None:
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_('Clip: "%s"'), 'utf8')
            else:
                prompt = _('Clip: "%s"')
            self.lbKeywordsList.InsertStringItem(sys.maxint, '  ' + prompt % self.clipObj.id)

        self.lbKeywordsList.InsertStringItem(sys.maxint, '')

        # Add the keywords from the list to the display
        for kws in self.kwlist:
            self.lbKeywordsList.InsertStringItem(sys.maxint, kws.keywordPair)
        # Set the column size
        self.lbKeywordsList.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def OnRightDown(self, event):
        """ Right-click event --> Show popup menu """
        # Determine the item that has been right-clicked.  -1 indicates the click was not on an item.
        (x, y) = event.GetPosition()
        (id, flags) = self.lbKeywordsList.HitTest(wx.Point(x, y))
        # If a keyword (rather than a header line) is selected, enable the Delete option
        if id > 3:
            # Select the item that was clicked
            self.lbKeywordsList.SetItemState(id, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
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
                    self.lbKeywordsList.SetItemState(id, 0, wx.LIST_STATE_SELECTED)
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
        obj.lock_record()
        # Create/define the Keyword List Edit Form
        dlg = KeywordListEditForm.KeywordListEditForm(self.parent.parent, -1, _("Edit Keyword List"), obj, self.kwlist)
        # Show the Keyword List Edit Form and process it if the user selects OK
        if dlg.ShowModal() == wx.ID_OK:
            # Clear the local keywords list and repopulate it from the Keyword List Edit Form
            self.kwlist = []
            for kw in dlg.keywords:
                self.kwlist.append(kw)

            # Copy the local keywords list into the appropriate object and save that object
            obj.keyword_list = self.kwlist

            for (keywordGroup, keyword, clipNum) in dlg.keywordExamplesToDelete:
                # Load the specified Clip record
                tempClip = Clip.Clip(clipNum)
                # Prepare the Node List for removing the Keyword Example Node
                nodeList = (_('Keywords'), keywordGroup, keyword, tempClip.id)
                # Call the DB Tree's delete_Node method.  Include the Clip Record Number so the correct Clip entry will be removed.
                self.parent.GetPage(0).tree.delete_Node(nodeList, 'KeywordExampleNode', tempClip.number)

            obj.db_save()

            # Update the display to reflect changes in the Keyword List
            self.UpdateKeywords()

        # Unlock the appropriate record
        obj.unlock_record()

        # Free the memory used for the Keyword List Edit Form  
        dlg.Destroy()

    def OnDelete(self, event):
        """ Selecting 'Delete' from the popup menu deletes a keyword """
        # Delete the appropriate keyword
        # NOTE:  Because self.kwlist is just a pointer to the keyword list in the appropriate object,
        #        removing the keyword from the object also removes it from the local kwlist!

        # We must first determine what item has been selected.  ListCtrl makes this a bit awkward.
        # First, let's initialize a variable to a value that can't be gotten from the ListCtrl.
        selItem = -1
        # Now let's iterate through the ListCtrl ...
        for loop in range(self.lbKeywordsList.GetItemCount()):
            # ... looking for an item that is selected ...
            if self.lbKeywordsList.GetItemState(loop, wx.LIST_STATE_SELECTED) > 0:
                # ... and if we find one, remember its number and stop looking
                selItem = loop
                break
        # If we find a selected item ...
        if selItem > -1:
            # ... separate out the Keyword Group and the Keyword
            kwlist = string.split(self.lbKeywordsList.GetItemText(selItem), ':')
            kwg = string.strip(kwlist[0])
            kw = string.strip(kwlist[1])
            
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
                # Unlock the record
                self.clipObj.unlock_record()
            elif self.episodeObj != None:
                # Lock the record
                self.episodeObj.lock_record()
                # Remove the keyword from the object
                delResult = self.episodeObj.remove_keyword(kwg, kw)
                # Save the object
                self.episodeObj.db_save()
                # Unlock the record
                self.episodeObj.unlock_record()

            # Update the display to reflect changes in the Keyword List
            self.UpdateKeywords()
