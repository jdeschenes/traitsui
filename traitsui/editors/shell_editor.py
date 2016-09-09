#-------------------------------------------------------------------------
#
#  Copyright (c) 2005, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#  Author: David C. Morrill
#  Date:   09/27/2005
#
#-------------------------------------------------------------------------

""" Editor that displays an interactive Python shell.
"""

#-------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------

from __future__ import absolute_import

import six

from traits.api import Bool, Str, Event, Property

from ..editor import Editor

from ..basic_editor_factory import BasicEditorFactory

from ..toolkit import toolkit_object


#-------------------------------------------------------------------------
#  'ShellEditor' class:
#-------------------------------------------------------------------------

class _ShellEditor(Editor):
    """ Base class for an editor that displays an interactive Python shell.
    """

    #-------------------------------------------------------------------------
    #  Trait definitions:
    #-------------------------------------------------------------------------

    # An event fired to execute a command in the shell.
    command_to_execute = Event()

    # An event fired whenver the user executes a command in the shell:
    command_executed = Event(Bool)

    # Is the shell editor is scrollable? This value overrides the default.
    scrollable = True

    #-------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #-------------------------------------------------------------------------

    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        # Moving the import here, since PythonShell is implemented in the
        # Pyface backend packages, and we want to delay loading this toolkit
        # specific class until this editor is actually used.
        from pyface.python_shell import PythonShell

        locals = None
        value = self.value
        if self.factory.share and isinstance(value, dict):
            locals = value
        self._shell = shell = PythonShell(parent, locals=locals)
        self.control = shell.control
        if locals is None:
            object = self.object
            shell.bind('self', object)
            shell.on_trait_change(self.update_object, 'command_executed',
                                  dispatch='ui')
            if not isinstance(value, dict):
                object.on_trait_change(self.update_any, dispatch='ui')
            else:
                self._base_locals = locals = {}
                for name in six.iterkeys(self._shell.interpreter().locals):
                    locals[name] = None

        # Synchronize any editor events:
        self.sync_value(self.factory.command_to_execute,
                        'command_to_execute', 'from')
        self.sync_value(self.factory.command_executed,
                        'command_executed', 'to')

        self.set_tooltip()

    #-------------------------------------------------------------------------
    #  Handles the user entering input data in the edit control:
    #-------------------------------------------------------------------------

    def update_object(self, event):
        """ Handles the user entering input data in the edit control.
        """
        locals = self._shell.interpreter().locals
        base_locals = self._base_locals
        if base_locals is None:
            object = self.object
            for name in object.trait_names():
                if name in locals:
                    try:
                        setattr(object, name, locals[name])
                    except:
                        pass
        else:
            dic = self.value
            for name, value in six.iteritems(locals):
                if name not in base_locals:
                    try:
                        dic[name] = value
                    except:
                        pass

        self.command_executed = True

    #-------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #-------------------------------------------------------------------------

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        if self.factory.share:
            value = self.value
            if isinstance(value, dict):
                self._shell.interpreter().locals = value
        else:
            locals = self._shell.interpreter().locals
            base_locals = self._base_locals
            if base_locals is None:
                object = self.object
                for name in object.trait_names():
                    locals[name] = getattr(object, name, None)
            else:
                dic = self.value
                for name, value in six.iteritems(dic):
                    locals[name] = value

    #-------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #-------------------------------------------------------------------------

    def update_any(self, object, name, old, new):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        locals = self._shell.interpreter().locals
        if self._base_locals is None:
            locals[name] = new
        else:
            self.value[name] = new

    #-------------------------------------------------------------------------
    #  Disposes of the contents of an editor:
    #-------------------------------------------------------------------------

    def dispose(self):
        """ Disposes of the contents of an editor.
        """
        self._shell.on_trait_change(self.update_object, 'command_executed',
                                    remove=True)
        if self._base_locals is None:
            self.object.on_trait_change(self.update_any, remove=True)

        super(_ShellEditor, self).dispose()

    #-------------------------------------------------------------------------
    #  Restores any saved user preference information associated with the
    #  editor:
    #-------------------------------------------------------------------------

    def restore_prefs(self, prefs):
        """ Restores any saved user preference information associated with the
            editor.
        """
        control = self._shell.control
        try:
            control.history = prefs.get('history', [])
            control.historyIndex = prefs.get('historyIndex', -1)
        except:
            pass

    #-------------------------------------------------------------------------
    #  Returns any user preference information associated with the editor:
    #-------------------------------------------------------------------------

    def save_prefs(self):
        """ Returns any user preference information associated with the editor.
        """
        control = self._shell.control
        return {'history': control.history,
                'historyIndex': control.historyIndex}

    #-------------------------------------------------------------------------
    #  Handles the 'command_to_execute' trait being fired:
    #-------------------------------------------------------------------------

    def _command_to_execute_fired(self, command):
        """ Handles the 'command_to_execute' trait being fired.
        """
        # Show the command. A 'hidden' command should be executed directly on
        # the namespace trait!
        self._shell.execute_command(command, hidden=False)

#-------------------------------------------------------------------------
#  Create the editor factory object:
#-------------------------------------------------------------------------

# Editor factory for shell editors.


class ToolkitEditorFactory(BasicEditorFactory):

    # The editor class to be instantiated.
    klass = Property

    # Should the shell interpreter use the object value's dictionary?
    share = Bool(False)

    # Extended trait name of the object event trait which triggers a command
    # execution in the shell when fired.
    command_to_execute = Str

    # Extended trait name of the object event trait which is fired when a
    # command is executed.
    command_executed = Str

    def _get_klass(self):
        """ Returns the toolkit-specific editor class to be used in the UI.
        """
        return toolkit_object('shell_editor:_ShellEditor')

# Define the ShellEditor
ShellEditor = ToolkitEditorFactory

### EOF ##################################################################
