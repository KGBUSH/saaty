# -*- coding: utf-8 -*-

from flask.signals import Namespace


__all__ = ['pre_init', 'post_init', 'pre_save', 'post_save', ]


_signals = Namespace()


pre_init = _signals.signal('model-pre-init')
post_init = _signals.signal('model-post-init')

pre_save = _signals.signal('model-pre-save')
post_save = _signals.signal('model-post-save')
