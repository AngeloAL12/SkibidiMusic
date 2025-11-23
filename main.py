import discord
from discord.ext import commands
import os
import shutil
import config

# --- DIAGNÓSTICO AL INICIO ---
print("🔍 DIAGNÓSTICO DE NODE:")
node_path = shutil.which("node") or shutil.which("nodejs")
print(f"👉 Python ve a Node en: {node_path}")

# --- CONFIGURACIÓN DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class SkibidiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents, help_command=None)

    async def setup_hook(self):
        # Cargar extensiones (Cogs)
        initial_extensions = ['cogs.music', 'cogs.general']
        
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ Extensión cargada: {extension}")
            except Exception as e:
                print(f"❌ Error cargando extensión {extension}: {e}")

    async def on_ready(self):
        print(f'--- {self.user} está conectado y listo en el Homelab ---')

        # Esto mostrará: "Escuchando !help"
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))

bot = SkibidiBot()

if __name__ == "__main__":
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN)
    else:
        print("❌ Error: No se encontró el token de Discord en .env")