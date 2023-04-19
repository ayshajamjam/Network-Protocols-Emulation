def checkPort(port):
    if (int(port) < 1024 or int(port) > 65535):
        print("Error: One or more port numbers are not in range [1024, 65535]")
        return False
    return True

def checkDropMethod(drop_method, drop_value):
    if(drop_method == '-p' and (drop_value < 0 or drop_value > 1)):
        print("Error: -p should have float value provided between 0 and 1")
        return False
    elif(drop_method != '-d' and drop_method != '-p'):
        print(drop_method)
        print("Error: Drop methods should be either -d or -p")
        return False
    else:
        return True