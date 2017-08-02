from roboragi.data_controller import PostgresController

async def postgres():
    return await PostgresController.get_instance()
    return
