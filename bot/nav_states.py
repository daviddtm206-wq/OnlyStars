"""
Sistema de estados de navegación para el bot OnlyStars
Implementa navegación jerárquica con menús y submenús
"""

from enum import Enum
from typing import List
from aiogram.fsm.context import FSMContext

class MenuState(Enum):
    """Estados de los diferentes menús del bot"""
    MAIN = "main"           # Menú principal
    CREATOR = "creator"     # Menú para creadores
    EXPLORE = "explore"     # Menú para explorar/fans
    ADMIN = "admin"         # Menú de administración
    HELP = "help"           # Menú de ayuda

class NavigationManager:
    """Gestiona la navegación entre menús usando FSM context"""
    
    NAV_STACK_KEY = "nav_stack"
    
    @classmethod
    async def push_state(cls, state: MenuState, context: FSMContext):
        """Agregar un nuevo estado al stack de navegación"""
        data = await context.get_data()
        nav_stack = data.get(cls.NAV_STACK_KEY, [])
        nav_stack.append(state.value)
        await context.update_data({cls.NAV_STACK_KEY: nav_stack})
    
    @classmethod
    async def pop_state(cls, context: FSMContext) -> MenuState:
        """Remover el estado actual y retornar al anterior"""
        data = await context.get_data()
        nav_stack = data.get(cls.NAV_STACK_KEY, [])
        
        if nav_stack:
            nav_stack.pop()  # Remover estado actual
        
        if nav_stack:
            current = nav_stack[-1]
        else:
            current = MenuState.MAIN.value
            nav_stack = [MenuState.MAIN.value]
        
        await context.update_data({cls.NAV_STACK_KEY: nav_stack})
        return MenuState(current)
    
    @classmethod
    async def get_current_state(cls, context: FSMContext) -> MenuState:
        """Obtener el estado actual de navegación"""
        data = await context.get_data()
        nav_stack = data.get(cls.NAV_STACK_KEY, [])
        
        if nav_stack:
            return MenuState(nav_stack[-1])
        else:
            return MenuState.MAIN
    
    @classmethod
    async def reset_to_main(cls, context: FSMContext):
        """Resetear navegación al menú principal"""
        await context.update_data({cls.NAV_STACK_KEY: [MenuState.MAIN.value]})
    
    @classmethod
    async def get_nav_path(cls, context: FSMContext) -> List[MenuState]:
        """Obtener el camino completo de navegación"""
        data = await context.get_data()
        nav_stack = data.get(cls.NAV_STACK_KEY, [MenuState.MAIN.value])
        return [MenuState(state) for state in nav_stack]