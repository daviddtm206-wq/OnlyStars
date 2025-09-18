# bot/videocall_system.py
import asyncio
import os
import uuid
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPrivileges
from pyrogram.errors import FloodWait, UserAlreadyParticipant
from database import (
    create_videocall_session, get_videocall_session, update_videocall_session_status,
    create_videocall_group, delete_videocall_group, get_videocall_settings
)

logger = logging.getLogger(__name__)

class VideoCallManager:
    def __init__(self):
        self.user_client = None
        self.bot_user_id = None
        self.initialized = False
        
    async def initialize(self, bot_user_id):
        """Inicializa el cliente de usuario de Pyrogram"""
        try:
            api_id = int(os.getenv("TELEGRAM_API_ID"))
            api_hash = os.getenv("TELEGRAM_API_HASH")
            phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")
            
            if not all([api_id, api_hash, phone_number]):
                logger.error("❌ Faltan credenciales de Telegram API para videollamadas")
                return False
            
            # Crear cliente de usuario con session file
            session_path = os.path.join(os.path.dirname(__file__), "videocall_session")
            self.user_client = Client(
                name=session_path,
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone_number
            )
            
            self.bot_user_id = bot_user_id
            logger.info("✅ VideoCallManager inicializado correctamente")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al inicializar VideoCallManager: {e}")
            return False
    
    async def create_videocall_group(self, session_id, creator_name):
        """Crea un grupo temporal para videollamada"""
        if not self.initialized:
            logger.error("❌ VideoCallManager no inicializado")
            return None
            
        try:
            async with self.user_client:
                # Crear título único para el grupo
                group_title = f"📹 Videollamada - {creator_name}"
                group_description = f"Sesión privada de videollamada • ID: {session_id}"
                
                # Crear supergrupo
                chat = await self.user_client.create_supergroup(
                    title=group_title,
                    description=group_description
                )
                
                # Promover bot como administrador con permisos de videollamada
                try:
                    await self.user_client.promote_chat_member(
                        chat_id=chat.id,
                        user_id=self.bot_user_id,
                        privileges=ChatPrivileges(
                            can_manage_video_chats=True,
                            can_restrict_members=True,
                            can_delete_messages=True,
                            can_invite_users=True
                        )
                    )
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo promover bot en grupo {chat.id}: {e}")
                
                # Registrar grupo en base de datos
                create_videocall_group(chat.id, session_id, group_title)
                
                logger.info(f"✅ Grupo creado: {group_title} (ID: {chat.id})")
                return chat.id
                
        except FloodWait as e:
            logger.warning(f"⚠️ Rate limit alcanzado, esperando {e.x} segundos...")
            await asyncio.sleep(e.x)
            return await self.create_videocall_group(session_id, creator_name)
            
        except Exception as e:
            logger.error(f"❌ Error al crear grupo para videollamada: {e}")
            return None
    
    async def invite_users_to_group(self, group_id, user_ids):
        """Invita usuarios al grupo de videollamada"""
        if not self.initialized:
            logger.error("❌ VideoCallManager no inicializado")
            return False
            
        try:
            async with self.user_client:
                for user_id in user_ids:
                    try:
                        await self.user_client.add_chat_members(
                            chat_id=group_id,
                            user_ids=[user_id]
                        )
                        logger.info(f"✅ Usuario {user_id} invitado al grupo {group_id}")
                        
                    except UserAlreadyParticipant:
                        logger.info(f"ℹ️ Usuario {user_id} ya está en el grupo {group_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error al invitar usuario {user_id}: {e}")
                        
                return True
                
        except Exception as e:
            logger.error(f"❌ Error general al invitar usuarios: {e}")
            return False
    
    async def delete_videocall_group(self, group_id):
        """Elimina grupo de videollamada después de la sesión"""
        if not self.initialized:
            logger.error("❌ VideoCallManager no inicializado")
            return False
            
        try:
            async with self.user_client:
                # Eliminar grupo
                await self.user_client.delete_supergroup(group_id)
                
                # Marcar como eliminado en base de datos
                delete_videocall_group(group_id)
                
                logger.info(f"✅ Grupo {group_id} eliminado correctamente")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error al eliminar grupo {group_id}: {e}")
            return False
    
    def generate_session_id(self):
        """Genera un ID único para la sesión de videollamada"""
        return f"vc_{uuid.uuid4().hex[:12]}"
    
    async def start_videocall_session(self, creator_id, fan_id, duration_minutes, price_stars, creator_name):
        """Inicia una sesión completa de videollamada"""
        try:
            # 1. Generar ID de sesión
            session_id = self.generate_session_id()
            
            # 2. Crear sesión en base de datos
            create_videocall_session(session_id, creator_id, fan_id, duration_minutes, price_stars)
            
            # 3. Crear grupo temporal
            group_id = await self.create_videocall_group(session_id, creator_name)
            if not group_id:
                return None, "❌ No se pudo crear el grupo de videollamada"
            
            # 4. Actualizar sesión con ID de grupo
            update_videocall_session_status(session_id, 'active', group_id)
            
            # 5. Invitar usuarios al grupo
            success = await self.invite_users_to_group(group_id, [creator_id, fan_id])
            if not success:
                await self.delete_videocall_group(group_id)
                return None, "❌ No se pudo invitar los usuarios al grupo"
            
            # 6. Programar eliminación automática del grupo
            asyncio.create_task(self._schedule_group_deletion(group_id, session_id, duration_minutes))
            
            logger.info(f"✅ Sesión de videollamada iniciada: {session_id}")
            return session_id, group_id
            
        except Exception as e:
            logger.error(f"❌ Error al iniciar sesión de videollamada: {e}")
            return None, f"Error interno: {str(e)}"
    
    async def _schedule_group_deletion(self, group_id, session_id, duration_minutes):
        """Programa la eliminación automática del grupo después de la duración"""
        try:
            # Esperar la duración de la videollamada + 5 minutos de gracia
            wait_seconds = (duration_minutes + 5) * 60
            await asyncio.sleep(wait_seconds)
            
            # Marcar sesión como completada
            update_videocall_session_status(session_id, 'completed')
            
            # Eliminar grupo
            await self.delete_videocall_group(group_id)
            
            logger.info(f"✅ Sesión {session_id} completada y grupo {group_id} eliminado")
            
        except Exception as e:
            logger.error(f"❌ Error en eliminación programada del grupo {group_id}: {e}")

# Instancia global del manejador de videollamadas
videocall_manager = VideoCallManager()