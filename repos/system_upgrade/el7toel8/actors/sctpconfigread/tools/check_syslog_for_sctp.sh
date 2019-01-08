#!/bin/sh

/usr/bin/journalctl --system -S '1 month ago' | /usr/bin/grep -m1 -w sctp

# Exit with success even if no match.
exit 0
