#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reports the progress of a plugin, or a plugins' tasks.
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
Golismero project mail: contact@golismero-project.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from threading import RLock


#------------------------------------------------------------------------------
class Progress (object):
    """
    Abstract class for progress monitors.
    """


    #--------------------------------------------------------------------------
    def __init__(self, **kwargs):
        """
        :keyword total: Total number of tasks.
        :type total: int

        :keyword completed: Number of tasks completed so far.
        :type completed: int

        :keyword percent: Initial percentage of completion.
        :type percent: float

        :keyword min_delta: Minimum delta percent needed to call the
            notify() method. Defaults to 0.0 (call on every change).
        """

        # Fetch the arguments.
        total     = kwargs.pop("total",     0)
        completed = kwargs.pop("completed", 0)
        percent   = kwargs.pop("percent",   0.0)
        min_delta = kwargs.pop("min_delta", 0.0)
        lock      = kwargs.pop("lock",      None)    # undocumented

        # Fail on unknown arguments.
        if kwargs:
            if len(kwargs) == 1:
                raise TypeError(
                    "Unknown keyword argument: %r" % list(kwargs)[0])
            raise TypeError(
                "Unknown keyword arguments: %s" %
                ", ".join(repr(k) for k in kwargs))

        # Sanitize the arguments.
        total     = int(total)       if total     else 0
        completed = int(completed)   if completed else 0
        percent   = float(percent)   if percent   else 0.0
        min_delta = float(min_delta) if min_delta else 0.0

        # Check the values.
        if total and total < 0:
            raise ValueError("Negative count of tasks: %r" % total)
        if completed and completed < 0:
            raise ValueError("Negative count of tasks: %r" % completed)
        if percent and (percent < 0.0 or percent > 100.0):
            raise ValueError("Invalid percent value: %r" % percent)
        if min_delta and (min_delta < 0.0 or min_delta > 100.0):
            raise ValueError("Invalid percent value: %r" % min_delta)

        # Deduce missing values.
        if total and completed and percent:
            if float(completed) * 100.0 / float(total) != percent:
                raise ValueError("Contradicting values")
        elif total and completed and not percent:
            percent = float(completed) * 100.0 / float(total)
        elif total and percent and not completed:
            completed = int( float(total) * percent / 100.0 )
        elif percent and completed and not total:
            total = int( float(completed) * 100.0 / percent )

        # Save the values.
        self.__total     = total
        self.__completed = completed
        self.__percent   = percent
        self.__min_delta = min_delta
        self._previous   = percent

        # Create or save the lock.
        self._lock = lock if lock else RLock()


    #--------------------------------------------------------------------------
    # Properties.

    @property
    def total(self):
        """
        :returns: Total number of tasks.
        :rtype: int
        """
        with self._lock:
            return self.__total

    @property
    def completed(self):
        """
        :returns: Number of tasks completed so far.
        :rtype: int
        """
        with self._lock:
            return self.__completed

    @property
    def percent(self):
        """
        :returns: Initial percentage of completion.
        :rtype: float
        """
        with self._lock:
            return self.__percent

    @property
    def min_delta(self):
        """
        :returns: Minimum delta percent needed to call the notify() method.
        :rtype: float
        """
        return self.__min_delta

    @min_delta.setter
    def min_delta(self, min_delta):
        """
        :param min_delta: Minimum delta percent needed to call the
            notify() method.
        :type min_delta: float
        """
        min_delta = float(min_delta) if min_delta else 0.0
        if min_delta and (min_delta < 0.0 or min_delta > 100.0):
            raise ValueError("Invalid percent value: %r" % min_delta)
        self.__min_delta = min_delta


    #--------------------------------------------------------------------------
    def set_total(self, total):
        """
        :param total: Total number of tasks.
        :type total: int
        """
        with self._lock:
            if total and total < 0:
                raise ValueError("Negative count of tasks: %r" % total)
            self.__total = total
            if self.__completed:
                self.__percent = float(self.__completed) * 100.0 / float(total)
                self.__refresh()
            elif self.__percent:
                self.__completed = int( float(total) * self.__percent / 100.0 )
            self.__refresh()


    #--------------------------------------------------------------------------
    def set_completed(self, completed):
        """
        :param completed: Number of tasks completed so far.
        :type completed: int
        """
        with self._lock:
            if completed and completed < 0:
                raise ValueError("Negative count of tasks: %r" % completed)
            self.__completed = completed
            if self.__total:
                self.__percent = float(completed) * 100.0 / float(self.__total)
                self.__refresh()
            elif self.__percent:
                self.__total = int( float(completed) * 100.0 / self.__percent )


    #--------------------------------------------------------------------------
    def set_percent(self, percent):
        """
        :param percent: Percentage of completion.
        :type percent: float
        """
        with self._lock:
            if percent and (percent < 0.0 or percent > 100.0):
                raise ValueError("Invalid percent value: %r" % percent)
            self.__percent = percent
            if self.__total:
                self.__completed = int( float(self.__total) * percent / 100.0 )
            elif self.__completed:
                self.__total = int( float(self.__completed) * 100.0 / percent )
            self.__refresh()


    #--------------------------------------------------------------------------
    def add_completed(self, delta = 1):
        """
        Add the value to the number of tasks completed.

        :param delta: Number of tasks completed to add.
        :type delta: int

        :returns: New value.
        :rtype: int
        """
        if delta:
            delta = int(delta)
            with self._lock:
                self.set_completed(self.__completed + delta)


    #--------------------------------------------------------------------------
    def add_percent(self, delta):
        """
        Add the given percent to the current value.

        :param delta: Percentage of completion to add.
        :type delta: float

        :returns: New value.
        :rtype: float
        """
        if delta:
            delta = float(delta)
            if delta < 100.0 or delta > 100.0:
                raise ValueError("Invalid delta percent value: %r" % delta)
            with self._lock:
                self.set_percent(self.__percent + delta)


    #--------------------------------------------------------------------------
    def begin_subtask(self, task_percent, **kwargs):
        """
        Create a new progress notifier for a subtask within another task.

        .. note: This is almost an alias of: TaskProgress(self, ...).
                 The difference is, this method adds up all the task
                 percentages you specify, and if they don't add up
                 an exception is raised.

        :param task_percent: Percentage of the parent progress represented by
            this task.
        :type task_percent: float

        """
        return TaskProgress(self, task_percent, **kwargs)

    # Patch the documentation.
    begin_subtask.__doc__ += __init__.__doc__


    #--------------------------------------------------------------------------
    def __refresh(self):
        ".. warning: Called internally, do not call it yourself!"
        if self._previous != self.__percent:
            min_delta = self.min_delta
            if (
                not min_delta or
                abs(self.__percent - self._previous) >= min_delta
            ):
                try:
                    self._notify()
                finally:
                    self._previous = self.__percent


    #--------------------------------------------------------------------------
    def _notify(self):
        ".. warning: Called internally, do not call it yourself!"
        raise NotImplementedError("Please use PluginProgress or TaskProgress!")


#------------------------------------------------------------------------------
class TaskProgress (Progress):
    """
    Divides a task into subtasks.
    """


    #--------------------------------------------------------------------------
    def __init__(self, parent, task_percent, **kwargs):
        """
        :param parent: Parent Progress object.
        :type parent: Progress

        :param task_percent: Percentage of the parent progress represented by
            this task.
        :type task_percent: float

        """

        # Check the values.
        task_percent = float(task_percent)
        if task_percent and (task_percent < 0.0 or task_percent > 100.0):
            raise ValueError("Invalid percent value: %r" % task_percent)
        if not isinstance(parent, Progress):
            raise TypeError("Expected Progress, got %r instead" % type(parent))

        # Save the values.
        self.__parent       = parent
        self.__task_percent = task_percent

        # Inherit the lock object of the parent.
        kwargs["lock"] = parent._lock

        # Call the parent constructor.
        super(TaskProgress, self).__init__(**kwargs)


    # Patch the documentation.
    __init__.__doc__ += Progress.__init__.__doc__


    #--------------------------------------------------------------------------
    # Properties.

    @property
    def parent(self):
        """
        :returns: Parent Progress object.
        :rtype: Progress
        """
        return self.__parent

    @property
    def task_percent(self):
        """
        :returns: Percentage of the parent progress represented by this task.
        :rtype: float
        """
        return self.__task_percent


    #--------------------------------------------------------------------------
    def _notify(self):
        delta = self.percent - self._previous
        delta = (delta * self.task_percent) / 100.0
        self.parent.add_percent(delta)
