from app.agents.worklow import IntentSchema


def test_dict_to_intent_schema():
    value = {
        'task': 'Add a button to view product uploaded image',
        'screen': 'Product Page',
        'application': 'Order Management System'
    }

    actual = IntentSchema(**value)

    assert actual is not None
    assert actual.task == 'Add a button to view product uploaded image'