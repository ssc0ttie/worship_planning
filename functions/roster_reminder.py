import pywhatkit


def test_reminder():

    # Send message to a WhatsApp number at 10:30 PM
    # pywhatkit.sendwhatmsg(
    #     "+6587935744",
    #     "Hi Scott! Please submit your availability today 😊",
    #     15,
    #     45,
    #     30,
    #     True,
    #     2,
    # )

    pywhatkit.sendwhatmsg_to_group(
        "JXW8HZJTn38ABURMLMMVEa",
        "This is a test please ignore : Please submit your availability today 😊",
        15,
        54,
        30,
        True,
        2,
    )


test_reminder()
