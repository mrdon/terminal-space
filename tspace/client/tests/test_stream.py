from tspace.client.stream import ANSICursor


def test_ansi_cursor():
    input_str = (
        "1b:5b:33:38:3b:32:3b:31:36:35:3b:31:36:35:3b:31:36:35:6d:57:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:31:36:"
        "35:3b:31:36:35:3b:31:36:35:6d:61:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:31:38:33:3b:31:38:33:3b:31:38:33:"
        "6d:72:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:35:6d:258c:1b:5b:30:6d:1b:5b:"
        "33:38:3b:32:3b:31:38:33:3b:31:38:33:3b:31:38:33:6d:69:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:36:38:3b:31:"
        "30:31:3b:31:39:35:6d:258e:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:35:6d:67:"
        "1b:5b:30:6d:1b:5b:33:38:3b:32:3b:31:38:33:3b:31:38:33:3b:31:38:33:6d:20:1b:5b:30:6d:1b:5b:33:38:3b:"
        "32:3b:31:38:33:3b:31:38:33:3b:31:38:33:6d:74:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:"
        "3b:32:35:35:6d:258c:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:35:6d:258c:1b:5b:"
        "30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:35:6d:258c:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:"
        "36:38:3b:31:30:31:3b:31:39:35:6d:258e:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:"
        "35:6d:258c:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:31:39:3b:32:31:39:3b:32:31:39:6d:74:1b:5b:30:6d:1b:5b:"
        "33:38:3b:32:3b:32:35:35:3b:32:35:35:3b:32:35:35:6d:6f:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:30:31:3b:"
        "32:30:31:3b:32:30:31:6d:72:1b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:31:39:3b:32:31:39:3b:32:31:39:6d:20:1"
        "b:5b:30:6d:1b:5b:33:38:3b:32:3b:32:30:31:3b:32:30:31:3b:32:30:31:6d:32:1b:5b:30:6d"
    )
    input_bytes = "".join([chr(int(i, 16)) for i in input_str.split(":")])

    assert [] == ANSICursor(input_bytes).parsed
