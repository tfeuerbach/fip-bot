# app/commands/__init__.py

from .fip_join import register_fip_join
from .fip_leave import register_fip_leave

def setup_commands(bot):
    register_fip_join(bot)
    register_fip_leave(bot)