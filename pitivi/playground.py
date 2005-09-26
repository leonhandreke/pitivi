#!/usr/bin/python
# PiTiVi , Non-linear video editor
#
#       playground.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gobject
import gst
from bin import SmartBin, SmartDefaultBin, SmartFileBin#, SmartTempUriBin

class PlayGround(gobject.GObject):
    """
    Holds all the applications pipelines in a GstThread.
    They all share the same (audio,video) sink threads.
    Only one pipeline uses those sinks at any given time, but other pipelines
    can be in a PLAYED state (because they can be encoding).

    Only SmartBin can be added to the PlayGround

    Signals:
      current-changed : There's a new bin playing
      current-state : The state of the current bin has changed
    """

    __gsignals__ = {
        "current-changed" : ( gobject.SIGNAL_RUN_LAST,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_PYOBJECT, )),
        "current-state" : ( gobject.SIGNAL_RUN_LAST,
                            gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT, )),
        "bin-added" : ( gobject.SIGNAL_RUN_LAST,
                       gobject.TYPE_NONE,
                       ( gobject.TYPE_PYOBJECT, )),
        "bin-removed" : ( gobject.SIGNAL_RUN_LAST,
                          gobject.TYPE_NONE,
                          ( gobject.TYPE_PYOBJECT, ))
        }

    # TODO
    #
    # * Only put in the thread what is being played/rendered
    #   The rest should only be remembered in the playground itself
    
    def __init__(self):
        gst.info("Starting up playground")
        gobject.GObject.__init__(self)
        # List of used pipelines
        self.pipelines = []
        
        self.playthread = gst.Pipeline("playground-thread")
        #        self.playthread.connect("element-added", self._reset_scheduler_clock)
        self.vsinkthread = None
        self.asinkthread = None
        
        # Defaut pipeline if no other pipeline is playing
        self.default = SmartDefaultBin()

        # Current playing pipeline
        self.current = None
        self.currentstart = 0
        self.currentlength = 0
        self.currentpos = 0
        self.tempsmartbin = None
        self.cur_state_signal = None
        self.cur_eos_signal = None
        
        self.switch_to_default()
        self.state = gst.STATE_READY
        self.playthread.set_state(self.state)

    def add_pipeline(self, pipeline):
        """ add a pipeline to the playground """
        gst.debug("pipeline : %s" % pipeline)
        if not isinstance(pipeline, SmartBin):
            return
        #self.playthread.add(pipeline)
        self.pipelines.append(pipeline)
        self.emit("bin-added", pipeline)

    def remove_pipeline(self, pipeline):
        """ removes a pipeline from the playground """
        gst.debug("pipeline : %s" % pipeline)
        if not pipeline in self.pipelines:
            return
        pipeline.set_state(gst.STATE_READY)
        if self.current == pipeline:
            self.switch_to_default()
        #self.playthread.remove(pipeline)
        self.pipelines.remove(pipeline)
        self.emit("bin-removed", pipeline)

    def switch_to_pipeline(self, pipeline):
        """ switch to the given pipeline for play output """
        gst.debug("pipeline : %s" % pipeline)
        if self.current == pipeline:
            return
        if not pipeline in self.pipelines and not pipeline == self.default:
            return
        if self.current:
            self.current.set_state(gst.STATE_PAUSED)
            self.vsinkthread.set_state(gst.STATE_READY)
            self.asinkthread.set_state(gst.STATE_READY)
            self.current.remove_audio_sink_thread()
            self.current.remove_video_sink_thread()
            if self.cur_state_signal:
                self.current.disconnect(self.cur_state_signal)
            if self.cur_eos_signal:
                self.current.disconnect(self.cur_eos_signal)
            self.playthread.remove(self.current)
            # remove the tempsmartbin if it's the current
            if self.current == self.tempsmartbin:
                self.tempsmartbin = None

        self.playthread.add(pipeline)
        self.current = pipeline
        self.current.set_state(gst.STATE_PAUSED)
        if self.current.has_video and self.vsinkthread:
            self.vsinkthread.set_state(gst.STATE_READY)
            self.current.set_video_sink_thread(self.vsinkthread)
        if self.current.has_audio and self.asinkthread:
            self.asinkthread.set_state(gst.STATE_READY)
            self.current.set_audio_sink_thread(self.asinkthread)
        self.emit("current-changed", self.current)
        self.cur_state_signal = self.current.connect("state-changed", self._current_state_change_cb)
        ## FIXME : eos signal doesn't exist anymore
        #self.cur_eos_signal = self.current.connect("eos", self._current_eos_cb)
        self.current.set_state(gst.STATE_PAUSED)

    def switch_to_default(self):
        """ switch to the default pipeline """
        gst.debug("switching to default")
        self.switch_to_pipeline(self.default)
        #self.default.set_state(gst.STATE_PLAYING)

##     def _reset_scheduler_clock(self, playthread, element_added):
##         # hack for 0.8
##         sched = self.playthread.get_scheduler()
##         clock = sched.get_clock()
##         sched.set_clock(clock)

    def set_video_sink_thread(self, vsinkthread):
        """ sets the video sink thread """
        gst.debug("video sink thread : %s" % vsinkthread)
        if self.vsinkthread and self.current:
            self.current.set_state(gst.STATE_PAUSED)
            self.current.remove_video_sink_thread()
        self.vsinkthread = vsinkthread
        if self.current:
            self.current.set_video_sink_thread(self.vsinkthread)
            self.current.set_state(gst.STATE_PAUSED)

    def set_audio_sink_thread(self, asinkthread):
        """ sets the audio sink thread """
        gst.debug("set audio sink thread : %s" % asinkthread)
        if self.asinkthread and self.current:
            self.current.set_state(gst.STATE_PAUSED)
            self.current.remove_audio_sink_thread()
        self.asinkthread = asinkthread
        if self.current:
            self.current.set_audio_sink_thread(self.asinkthread)
            self.current.set_state(gst.STATE_PAUSED)

    def _play_temporary_bin(self, tempbin):
        """ temporarely play a smartbin """
        gst.debug("tempbin : %s" % tempbin)
        self.pause()
        self.add_pipeline(tempbin)
        self.switch_to_pipeline(tempbin)
        if self.tempsmartbin:
            self.remove_pipeline(self.tempsmartbin)
        self.tempsmartbin = tempbin
        self.play()        

    def play_temporary_uri(self, uri):
        """ plays a uri """
        gst.debug("uri : %s" % uri)
        tempbin = SmartTempUriBin(uri)
        self._play_temporary_bin(tempbin)
        pass

    def play_temporary_filesourcefactory(self, factory):
        """ temporarely play a FileSourceFactory """
        gst.debug("factory : %s" % factory)
        if isinstance(self.current, SmartFileBin) and self.current.factory == factory:
            return
        tempbin = SmartFileBin(factory)
        self._play_temporary_bin(tempbin)

    def seek_in_current(self, value):
        """ seek to the given position in the current playing bin """
        gst.debug("value : %s" % value) 
        if not self.current:
            return
##         prevstate = self.current.get_state()
##         if not prevstate == gst.STATE_PAUSED:
##             self.current.set_state(gst.STATE_PAUSED)
        prevstate = self.state
        if not prevstate == gst.STATE_PAUSED:
            self.pause()
        if not self.vsinkthread.seek(gst.SEEK_METHOD_SET | gst.FORMAT_TIME | gst.SEEK_FLAG_FLUSH,
                                     value):
            gst.error("COULDN'T SEEK !!!!!!!")
        if not self.asinkthread.seek(gst.SEEK_METHOD_SET | gst.FORMAT_TIME | gst.SEEK_FLAG_FLUSH,
                                     value):
            gst.error("COULDN'T SEEK !!!!!!!")
        if prevstate == gst.STATE_PLAYING:
            self.play()
##         if not prevstate == gst.STATE_PAUSED:
##             self.current.set_state(prevstate)

    def _current_state_change_cb(self, current, prevstate, newstate):
        current.debug("changed state from %s to %s" % (prevstate, newstate))
        if newstate in [int(gst.STATE_PAUSED), int(gst.STATE_PLAYING)]:
            if newstate == int(gst.STATE_PAUSED):
                self.state = gst.STATE_PAUSED
            else:
                self.state = gst.STATE_PLAYING
            self.emit("current-state", newstate)

##     def _current_eos_cb(self, current):
##         print current, "has EOS!"
##         self.emit("current-state", gst.STATE_READY)

    #
    # playing proxy functions
    #

    def play(self):
        """ play the current pipeline """
        gst.debug("play")
        if not self.current or not self.asinkthread or not self.vsinkthread:
            gst.warning("returning ???")
            return
        if not self.state == gst.STATE_PLAYING:
            gst.debug("setting to play")
            #self.vsinkthread.set_state(gst.STATE_PLAYING)
            #self.asinkthread.set_state(gst.STATE_PLAYING)
            #self.current.set_state(gst.STATE_PLAYING)
            self.state = gst.STATE_PLAYING
            self.playthread.set_state(self.state)

    def pause(self):
        """ pause the current pipeline """
        gst.debug("pause")
        if not self.current or self.current == self.default:
            return
        if not self.state == gst.STATE_PAUSED:
            #self.current.set_state(gst.STATE_PAUSED)
            self.state = gst.STATE_PAUSED
            self.playthread.set_state(self.state)

    def fast_forward(self):
        """ fast forward the current pipeline """
        pass

    def rewind(self):
        """ play the current pipeline backwards """
        pass

    def forward_one(self):
        """ forward the current pipeline by one video frame """
        pass

    def backward_one(self):
        """ rewind the current pipeline by one video frame """
        pass

    def seek(self, time):
        """ seek in the current pipeline """
        pass

gobject.type_register(PlayGround)
