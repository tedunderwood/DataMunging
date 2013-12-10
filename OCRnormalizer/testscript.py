def main():
    import os
    
    j = os.getcwd()
    jpar = os.path.abspath(os.path.join(j, os.pardir))
    print(j, jpar)

    filelist = list()
    for root, dirs, files in os.walk(j):
        for file in files:
            if len(file) > 4 and (file[-4:] == ".txt" or file[-4:] == ".zip"):
                filepath = os.path.join(root, file)
                filelist.append(filepath)

    for path in filelist:
        print(path)

if __name__ == "__main__":
    main()
