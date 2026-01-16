import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread        



TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.message_content = True  # Necesario para recibir mensajes

bot = commands.Bot(command_prefix='¡', intents=intents)

# Diccionario para almacenar la configuración TEMPORAL (mientras configuras)
# pending_config = {
#     guild_id: {
#         'channel_id': 123456,
#         'roles': {'emoji': role_id}
#     }
# }
pending_config = {}

# Diccionario para almacenar la configuración ACTIVA (mensajes ya enviados)
# active_messages = {
#     message_id: {
#         'guild_id': 123456,
#         'roles': {'emoji': role_id}
#     }
# }
active_messages = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def canal(ctx, channel_id: int):
    guild_id = ctx.guild.id
    if guild_id not in pending_config:
        pending_config[guild_id] = {'channel_id': None, 'roles': {}}
    pending_config[guild_id]['channel_id'] = channel_id
    await ctx.send(f'Canal de reacciones establecido a {channel_id} para el próximo mensaje.')

@bot.command()
async def rol(ctx, role: discord.Role, emoji: str):
    guild_id = ctx.guild.id
    if guild_id not in pending_config:
        pending_config[guild_id] = {'channel_id': None, 'roles': {}}
    pending_config[guild_id]['roles'][emoji] = role.id
    await ctx.send(f'Rol {role.name} asignado al emoji {emoji} (Pendiente de enviar)')

@bot.command()
async def mensaje_reaccion(ctx, *, mensaje: str):
    guild_id = ctx.guild.id
    
    # Verificamos si hay configuración pendiente para este servidor
    if guild_id not in pending_config or not pending_config[guild_id]['channel_id']:
        await ctx.send('No has configurado el canal. Usa !canal <id> primero.')
        return

    channel_id = pending_config[guild_id]['channel_id']
    roles_config = pending_config[guild_id]['roles']

    if not roles_config:
        await ctx.send('No has configurado ningún rol. Usa !rol @rol <emoji> primero.')
        return

    channel = bot.get_channel(channel_id)
    if channel:
        try:
            # 1. Enviar el mensaje
            msg = await channel.send(mensaje)
            
            # 2. Añadir las reacciones visuales
            for emoji in roles_config.keys():
                await msg.add_reaction(emoji)
            
            # 3. GUARDAR en la memoria permanente vinculada al ID del mensaje
            active_messages[msg.id] = {
                'guild_id': guild_id,
                'roles': roles_config.copy() # Hacemos una copia para que sea independiente
            }

            # 4. LIMPIAR la configuración pendiente para empezar de cero la próxima vez
            pending_config[guild_id]['roles'] = {} 
            # (Opcional: ¿Quieres borrar también el canal? De momento solo borro los roles)
            
            await ctx.send(f'Mensaje enviado y configuración guardada. ID: {msg.id}')
        except Exception as e:
             await ctx.send(f'Error al enviar mensaje o reacciones: {e}')
    else:
        await ctx.send('No se pudo encontrar el canal configurado.')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    # Buscamos la configuración directamente por el ID del Mensaje
    if payload.message_id in active_messages:
        message_config = active_messages[payload.message_id]
        
        # Obtenemos el rol asociado a ese emoji en ESE mensaje específico
        role_id = message_config['roles'].get(payload.emoji.name)
        
        if role_id:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.add_roles(role)
                    print(f'Rol {role.name} añadido a {member.name} (Mensaje: {payload.message_id})')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    if payload.message_id in active_messages:
        message_config = active_messages[payload.message_id]
        role_id = message_config['roles'].get(payload.emoji.name)
        
        if role_id:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)
                    print(f'Rol {role.name} removido de {member.name} (Mensaje: {payload.message_id})')



app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()



keep_alive()

bot.run(TOKEN)