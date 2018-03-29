# -*- coding: utf-8 -*-

import core

app = core.setup()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=app.debug)
