from datetime import datetime
import uuid
from sqlalchemy import desc, select, update
from sqlalchemy.orm import joinedload

from lib.db_connection import async_session

from lib.models import JBPluginUUID, JBSession, JBTurn, JBUser, JBMessage, JBBot


async def create_user(
    bot_id: str, phone_number: str, first_name: str, last_name: str
) -> JBUser:
    user_id = str(uuid.uuid4())
    user = JBUser(
        id=user_id,
        bot_id=bot_id,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name,
    )
    async with async_session() as session:
        async with session.begin():
            session.add(user)
            await session.commit()
            return user
    return None


async def get_user_by_number(number: str, bot_id: str) -> JBUser:
    query = select(JBUser).where(
        JBUser.phone_number == number and JBUser.bot_id == bot_id
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            user = result.scalars().first()
            return user
    return None


async def create_session(pid: str, bot_id: str):
    session_id = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            s = JBSession(id=session_id, pid=pid, bot_id=bot_id)
            session.add(s)
            await session.commit()
            return s
    return None


async def get_user_session(bot_id: str, pid: str, timeout: int):
    query = (
        select(JBSession)
        .where(JBSession.pid == pid and JBSession.bot_id == bot_id)
        .order_by(desc(JBSession.created_at))
    )
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            session = result.scalars().first()
            if session is not None:
                if (
                    session.created_at.timestamp() + timeout
                    > datetime.now().timestamp()
                ):
                    return session
    return None


async def update_session(session_id: str):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(JBSession)
                .where(JBSession.id == session_id)
                .values(updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()
            return session_id
    return None


async def create_turn(session_id: str, bot_id: str, turn_type: str, channel: str):
    turn_id: str = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            session.add(
                JBTurn(
                    id=turn_id,
                    session_id=session_id,
                    bot_id=bot_id,
                    turn_type=turn_type,
                    channel=channel,
                )
            )
            await session.commit()
            return turn_id
    return None


async def create_message(
    turn_id: str,
    message_type: str,
    channel: str,
    channel_id: str,
    is_user_sent: bool = False,
):
    message_id = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            session.add(
                JBMessage(
                    id=message_id,
                    turn_id=turn_id,
                    message_type=message_type,
                    channel=channel,
                    channel_id=channel_id,
                    is_user_sent=is_user_sent,
                )
            )
            await session.commit()
            return message_id
    return None


async def get_bot_by_id(bot_id: str):
    query = select(JBBot).where(JBBot.id == bot_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            bot = result.scalars().first()
            return bot
    return None

async def get_bot_phone_number(phone_number):
    query = select(JBBot).where(JBBot.phone_number == phone_number and JBBot.status == 'active')
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            bot = result.scalars().first()
            return bot.id if bot else None
    return None


async def get_chat_history(bot_id: str, skip=0, limit=1000):
    # TODO: introduce pagination
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                        select(JBSession)
                        .options(joinedload(JBSession.user))
                        .join(JBUser, JBSession.pid == JBUser.id)
                        .where(JBSession.bot_id == bot_id)
                        .offset(skip)
                        .limit(limit)
                    )
            chat_history = result.scalars().all()
            return chat_history
    return None

async def get_plugin_reference(plugin_uuid: str) -> JBPluginUUID:
    # Create a query to select JBPluginMapping based on the provided plugin_uuid
    query = select(JBPluginUUID).where(JBPluginUUID.id == plugin_uuid)

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s
    return None

async def get_bot_list():
    async with async_session() as session:
        async with session.begin():
            query = select(JBBot).where(JBBot.status != 'deleted')
            result = await session.execute(query)
            bot_list = result.scalars().all()
            return bot_list
    return None


async def get_bot_chat_sessions(bot_id: str, session_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .filter(JBSession.bot_id == bot_id)
                .options(
                    joinedload(JBSession.user),
                    joinedload(JBSession.turns).joinedload(JBTurn.messages)
                ).where(JBSession.id == session_id)
            )
            chat_sessions = result.unique().scalars().all()
            return chat_sessions
    return None

async def update_bot(bot_id: str, data):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(JBBot)
                .where(JBBot.id == bot_id)
                .values(data)
            )
            await session.execute(stmt)
            await session.commit()
            return bot_id
    return None

async def create_bot(data):
    bot_id = str(uuid.uuid4())
    bot = JBBot(id=bot_id, **data)
    async with async_session() as session:
        async with session.begin():
            session.add(bot)
            await session.commit()
            return bot
    return None