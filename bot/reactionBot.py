import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv



TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.message_content = True  # Necesario para recibir mensajes

bot = commands.Bot(command_prefix='¡', intents=intents)

# Diccionario para almacenar los roles y emojis por servidor
guild_role_emojis = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def canal(ctx, channel_id: int):
    guild_id = ctx.guild.id
    if guild_id not in guild_role_emojis:
        guild_role_emojis[guild_id] = {'channel_id': None, 'role_emojis': {}}
    guild_role_emojis[guild_id]['channel_id'] = channel_id
    await ctx.send(f'Canal de reacciones establecido a {channel_id}')

@bot.command()
async def rol(ctx, role: discord.Role, emoji: str):
    guild_id = ctx.guild.id
    if guild_id not in guild_role_emojis:
        guild_role_emojis[guild_id] = {'channel_id': None, 'role_emojis': {}}
    guild_role_emojis[guild_id]['role_emojis'][emoji] = role.id
    await ctx.send(f'Rol {role.name} asignado al emoji {emoji}')

@bot.command()
async def mensaje_reaccion(ctx, *, mensaje: str):
    guild_id = ctx.guild.id
    if guild_id in guild_role_emojis and guild_role_emojis[guild_id]['channel_id']:
        channel = bot.get_channel(guild_role_emojis[guild_id]['channel_id'])
        if channel:
            msg = await channel.send(mensaje)
            for emoji in guild_role_emojis[guild_id]['role_emojis'].keys():
                await msg.add_reaction(emoji)
            await ctx.send(f'Mensaje de reacción enviado en {channel.mention}')
        else:
            await ctx.send('Canal no encontrado. Asegúrate de haber establecido el canal correctamente.')
    else:
        await ctx.send('Canal no establecido. Usa el comando !canal para establecer el canal de reacciones.')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return  # Ignorar las reacciones añadidas por el bot

    guild_id = payload.guild_id
    if guild_id in guild_role_emojis and payload.channel_id == guild_role_emojis[guild_id]['channel_id']:
        role_id = guild_role_emojis[guild_id]['role_emojis'].get(payload.emoji.name)
        if role_id:
            guild = bot.get_guild(guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)
                print(f'Rol {role.name} añadido a {member.name}')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return  # Ignorar las reacciones eliminadas por el bot

    guild_id = payload.guild_id
    if guild_id in guild_role_emojis and payload.channel_id == guild_role_emojis[guild_id]['channel_id']:
        role_id = guild_role_emojis[guild_id]['role_emojis'].get(payload.emoji.name)
        if role_id:
            guild = bot.get_guild(guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)
                print(f'Rol {role.name} removido de {member.name}')

bot.run(TOKEN)