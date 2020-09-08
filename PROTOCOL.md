# Femtolytics Protocol

The endpoint of the API will be dependent on which instance of femtolytics you are using. If you are using your own instance, check your project's `urls.py` file to see the root path for `femtolytics.api.urls`.

If you are using [femtolytics.com](https://femtolytics.com) then the endpoint will be `https://femtolytics.com/api/v1/`

Femtolytics uses two types of events, one is called `event` for internal events, the other is called `action` for application specific actions.

`event` is meant for internal events and should not be triggered by direct calls from the application.

## Format

The API uses `POST` with `application/json` body.

There are common fields to the JSON dictionary sent that carries information about the application and the device.

The `package` dictionary has the information about the application, including the package name as defined in your iOS `Info.plist` or your Android `AndroidManifest.xml`.

*Note the `package` `name` has to be registered in the instance of `femtolytics` for the server to accept the events.*

## Timestamp

Timestamp are strings formatted in ISO8601.

## Visitor ID

Visitor ID is a unique identifier for the device. It should be generated upon installation of the application. In the protocol, it's a string and a hex representation of a UUID.

*Femtolytics is not using the Advertising tracking identifier which means that users are not tracked across devices or across re-installation of the application.*

## Event

To register events with femtolytics:

`POST` to `https://femtolytics.com/api/v1/event` a JSON dictionary with the `events` key and an arrary of events for value.

Example:
```json
{
    "events": [
        {
            "package": {
                "name": "com.example.app",
                "version": "1.2.3",
                "build": "456",
            },
            "device": {
                "name": "iPhone 11 Max",
                "physical": true,
                "os": "13.1.4",
            },
            "visitor_id": "uuid",
            "event": {
                "type": "<type>",
                "time": "<ISO8601 Time>",
                "properties": {},
            }
        }
    ]
}
```

In this particular case, `type` needs to be one of the followings `VIEW`, `NEW_USER`, `CRASH`, `GOAL`, `DETACHED`, `RESUMED`, `INACTIVE`, `PAUSED`

### `VIEW` 

To track application screens. Properties MUST contain `view`.

Example:
```json
    "event": {
        "type": "VIEW",
        "properties": {
            "view": "HomePage"
        },
        "time": "<time>"
    }
```

### `NEW_USER`

To notify the instance of a new installation. Properties MUST contain `visitor_id`.

Example:
```json
    "event": {
        "type": "NEW_USER",
        "properties": {
            "visitor_id": "<uuid>"
        },
        "time": "<time>"
    }
```

### `CRASH`

To notify of unhandled exceptions or crashes. Properties MUST contain `exception` and CAN contain `stack_trace`. The stack trace can be multiline.

Example
```json
    "event": {
        "type": "CRASH",
        "properties": {
            "exception": "Divide by zero",
            "strack_trace": "Filename:Line:divide_by\nFilename:Line:button_clicked\n"
        },
        "time": "<time>"
    }
```

### `GOAL`

To track goals such as in-app purchases or other conversion goals. Properties MUST contain `goal`. The application can provide additional properties (e.g. price)

Example:
```json
    "event": {
        "type": "GOAL",
        "properties": {
            "goal": "Subscription",
            "price": "USD9.99"
        },
        "time": "<time>"
    }
```

### `DETACHED`, `RESUMED`, `INACTIVE`, `PAUSED`

Used to track the lifecyle of the application.

## Action

To register custom actions:

`POST` to `https://femtolytics.com/api/v1/action` a JSON dictionary with the `actions` and an array of actions as value.

Example:
```json
{
    "actions": [
        {
            "package": {
                "name": "com.example.app",
                "version": "1.2.3",
                "build": "99",
            },
            "device": {
                "name": "iPhone 11 Max",
                "physical": true,
                "os": "13.1.4",
            },
            "visitor_id": "uuid",
            "action": {
                "type": "<type>",
                "time": "<ISO8601 Time>",
                "properties": {},
            }
        }
    ]
}
```

In this case the `type` of an action is free form and can be provided by the application (e.g. `Button Clicked`, `Registered`...) The `properties` field is optional and free form as well.