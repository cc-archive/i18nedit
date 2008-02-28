#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""provides a simple wrapper for composing and sending emails via smtp or MAPI"""

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

###################### SMTP code ######################

import smtplib
import socket
import mimetypes
from email.Encoders import encode_base64
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# some constants for messages
contentheader = \
"""Content-Type: %s;
	charset = "%s"
"""
mimeversion = "MIME-Version: 1.0\n"
contenttransferencoding = "Content-Transfer-Encoding: 8bit\n"

def makemessage(messagedict, attachmentlist=[]):
  #attachmentlist is a list of tuples containing the physical filename, and the required filename
  #eg. [('c:\\testme.pdf', 'testme.pdf'), ('c:\\oracle\\oradata\\mydb\\system01.dbf', 'reallybigspam.txt')]
  attachments = []
  for thefile in attachmentlist:    #make a list of attachments as text to be added
    attachments.append(makeAttachment(thefile[0], thefile[1]))
  messagecharset = messagedict.get('charset','utf8')
  message = contentheader % (messagedict.get('contenttype', 'text/plain'),
                             messagecharset)
  if 'from' in messagedict:
    message += "From: %s\n" % messagedict['from']
  if 'organization' in messagedict:
    message += "Organization: %s\n" % messagedict['organization']
  if 'to' in messagedict:
    recipients = messagedict['to']
    if isinstance(recipients, (str, unicode)):
      recipients = recipients.split(",")
    message += "To: %s\n" % ", ".join(recipients)
  if 'subject' in messagedict:
    message += "Subject: %s\n" % messagedict['subject']
  if 'reply-to' in messagedict:
    message += "Reply-To: %s\n" % messagedict['reply-to']
  try:
    import email.Utils
    message += "Date: %s\n" % email.Utils.formatdate(localtime=True)
  except:
    raise
  if attachmentlist:
    msgbody = MIMEMultipart()
    if 'body' in messagedict:
      msgbody.attach(MIMEText(messagedict['body']))
    for file in attachments:
      msgbody.attach(file)
    message += msgbody.as_string()
  else:
    message += mimeversion + contenttransferencoding + "\n"
    if 'body' in messagedict:
      message += messagedict['body']

  # Make sure the entire message is encoded using the stated charset
  message = message.encode(messagecharset)
  return message

def makeAttachment(attachedFile, Outfile):
    ctype = 'application/octet-stream'
    fileIn = open(attachedFile, 'rb')
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(fileIn.read())
    encode_base64(attachment)
    fileIn.close
    attachment.add_header('Content-Disposition', 'attachment',filename=Outfile)
    return attachment

def dosendmessage(fromemail,recipientemails,message,smtpserver='',errorhandler=None):
  smtp = smtplib.SMTP()
  errmsg = ""
  try:
    smtp.connect(smtpserver)
    refused = smtp.sendmail(fromemail,recipientemails,message)
    errmsg += ", ".join(refused.keys())
    if errmsg != "":
      errmsg = "Recipients " + errmsg + " refused"
  except smtplib.SMTPRecipientsRefused:
    errmsg += "All recipients refused"
  except smtplib.SMTPHeloError:
    errmsg += "Server didn't respond properly to HELO"
  except smtplib.SMTPSenderRefused:
    errmsg += "Sender refused"
  except smtplib.SMTPDataError:
    errmsg += "Unexpected error code"
  except UnicodeEncodeError:
      errmsg += "Error in transporting message due to a unicode encoding error"
      if errorhandler is not None:
        errmsg += ": %r" % errorhandler.exception_str()
  except socket.error, msg:
    if errorhandler is not None:
      errmsg += "Socket Error: %r" % errorhandler.exception_str()
  if smtp.sock:
    smtp.quit()
  if errmsg != "" and errorhandler is not None:
    errorhandler.logerror(errmsg)
  return errmsg

def SendSMTPMail(Subject="", Message="", SendTo=None, SendCC=None, SendBCC=None, SendFrom=None, SMTPServer=None, errorhandler=None):
  # currently SendFrom must be a tuple: label, address
  fromlabel, fromaddress = SendFrom
  toaddresses = ccaddresses = bccaddresses = []
  if SendTo is not None:
    toaddresses = [addr.strip() for addr in SendTo.split(",")]
  if SendCC is not None:  
    ccaddresses = [addr.strip() for addr in SendCC.split(",")]
  if SendBCC is not None:
    bccaddresses = [addr.strip() for addr in SendBCC.split(",")]
  recipients = toaddresses + ccaddresses + bccaddresses
  messagedict = {"from": "%s <%s>" % (fromlabel, fromaddress),
                 "to": toaddresses,
                 "cc": ccaddresses,
                 "bcc": bccaddresses,
                 "subject": Subject,
                 "body": Message}
  message = makemessage(messagedict)
  dosendmessage(fromaddress, recipients, message, SMTPServer, errorhandler)

###################### Simple MAPI code ######################

def SetRecipients(Message,Recipients,RecipientType):
   """add recipient names to list"""
   for recipient in Recipients.split(','):
      recip = Message.Recipients.Add(Name=recipient, Type=RecipientType)
      recip.Resolve()

def SendMAPIMail(Subject="", Message="", SendTo=None, SendCC=None, SendBCC=None, MAPIProfile=None):
   """method used to send mapi email, pass email address, subject, MAPIprofile and message"""
   # Create a mapi session
   import win32com.client.dynamic
   mapi = win32com.client.dynamic.Dispatch("MAPI.session")

   if MAPIProfile:
     mapi.Logon(MAPIProfile)
   else:
     mapi.Logon()

   # Create a new message
   outbox = mapi.OutBox.Messages.Add(Subject,Message,'CMC: IPM')

   # Set the recipients
   if SendTo:
     SetRecipients(outbox,SendTo,1)
   if SendCC:
     SetRecipients(outbox,SendCC,2)
   if SendBCC:
     SetRecipients(outbox,SendBCC,3)

   # Update and send the message
   outbox.Update()
   outbox.Send()
   mapi.DeliverNow()

   # terminate the MAPI session and kill the objects   
   mapi.Logoff()
   outbox = None
   mapi = None

###################### Extended MAPI code ######################


def SendEMAPIMail(Subject="", Message="", SendTo=None, SendCC=None, SendBCC=None, MAPIProfile=None):
    """
    Sends an email to the recipient using the extended MAPI interface
    """
    from win32com.mapi import mapi,mapitags,mapiutil

    # initialize and log on
    mapi.MAPIInitialize(None)
    session = mapi.MAPILogonEx(0, MAPIProfile, None, mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT)
    adminprofiles = mapi.MAPIAdminProfiles(0)
    messagestorestable = session.GetMsgStoresTable(0)
    statustable = session.GetStatusTable(0)
    messagestorestable.SetColumns((mapitags.PR_ENTRYID, mapitags.PR_DISPLAY_NAME_A, mapitags.PR_DEFAULT_STORE),0)

##    #this shows a how to make a restriction. it might be useful later
##    restrictionType = (mapi.RES_PROPERTY,(mapi.RELOP_EQ,mapitags.PR_DEFAULT_STORE,(mapitags.PT_BOOLEAN,True)))
##    messagestorestable.Restrict(restrictionType,0)

    while True:
        rows = messagestorestable.QueryRows(1, 0)
        #if this is the last row then stop
        if len(rows) != 1:
            break
        row = rows[0]
        #if this is the default store then stop
        if ((mapitags.PR_DEFAULT_STORE,True) in row):
            break

    # unpack the row and open the message store
    (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
    msgstore = session.OpenMsgStore(0,eid,None,mapi.MDB_NO_DIALOG | mapi.MAPI_BEST_ACCESS)

    # get the outbox
    hr, props = msgstore.GetProps((mapitags.PR_IPM_OUTBOX_ENTRYID), 0)
    (tag, eid) = props[0]
    #check for errors
    if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
        raise TypeError,'got PT_ERROR instead of PT_BINARY: %s'%eid
    outboxfolder = msgstore.OpenEntry(eid,None,mapi.MAPI_BEST_ACCESS)

    # create the message and the addrlist
    message = outboxfolder.CreateMessage(None,0)
   
    pal = []
    def makeentry(recipient, recipienttype):
      return ((mapitags.PR_RECIPIENT_TYPE, recipienttype),
              (mapitags.PR_SEND_RICH_INFO, False),
              (mapitags.PR_DISPLAY_TYPE, 0),
              (mapitags.PR_OBJECT_TYPE, 6),
              (mapitags.PR_EMAIL_ADDRESS_A, recipient),
              (mapitags.PR_ADDRTYPE_A, 'SMTP'),
              (mapitags.PR_DISPLAY_NAME_A, recipient))
    
    if SendTo:
      pal.extend([makeentry(recipient, mapi.MAPI_TO) for recipient in SendTo.split(",")])
    if SendCC:
      pal.extend([makeentry(recipient, mapi.MAPI_CC) for recipient in SendCC.split(",")])
    if SendBCC:
      pal.extend([makeentry(recipient, mapi.MAPI_BCC) for recipient in SendBCC.split(",")])

    #f = open('c:\\nexsig.gif')
    
    # add the resolved recipients to the message
    message.ModifyRecipients(mapi.MODRECIP_ADD,pal)
    #iAttach = message.CreateAttach(None,0)
    #iAttach[1].SetProps([(mapitags.NUM_ATT_PROPS, 5),
                         #(mapitags.PR_ATTACH_METHOD, mapi.ATTACH_BY_VALUE),
                         #(mapitags.PR_ATTACH_LONG_FILENAME, 'test.gif'),
                         #(mapitags.PR_ATTACH_FILENAME, 'test.gif'),
                         #(mapitags.PR_ATTACH_EXTENSION, '.gif'),
                         #(mapitags.PR_ATTACH_NUM, iAttach[0]),
                         #(mapitags.PR_DISPLAY_NAME, 'test.gif'),
                         #(mapitags.PR_ATTACH_DATA_BIN, f.read()),
                         #(mapitags.PR_ATTACH_ENCODING, 'FLAANSAAS'),
                         #])
    #f.close()
    message.SetProps([(mapitags.PR_BODY_A,Message),
                      (mapitags.PR_SUBJECT_A,Subject)])

    #iAttach[1].SaveChanges(0)
    # save changes and submit
    outboxfolder.SaveChanges(0)
    message.SubmitMessage(0)

def test():
   MAPIProfile = "mail.sjsoft.com"
   SendTo = "test@sjsoft.com"
   SendCC = None
   SendBCC = None
   SendMessage = "testing one two three"
   # SendSubject = "Testing Simple MAPI!!"
   # SendMAPIMail(SendSubject, SendMessage, SendTo, MAPIProfile=MAPIProfile)
   SendSubject = "Testing Extended MAPI!!"
   print SendSubject
   SendEMAPIMail(SendSubject, SendMessage, SendTo, MAPIProfile=MAPIProfile)

if __name__ == '__main__':
  test()

