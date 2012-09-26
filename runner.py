import sys


def main():

    # depends on tasks/[task_name].py being present relative to this directory
    sys.path.append("tasks")
    task_name = sys.argv[1]
    try:
        __import__(task_name).main(sys.argv[2:])
    except Exception as exception:
        raise exception

if __name__ == '__main__':
    main()
