import shutil

def remove_examples():
    shutil.rmtree("{{ cookiecutter.subnet_template_slug }}/api/examples")


def main():
    if "{{ cookiecutter.keep_examples }}".lower() == "n":
        remove_examples()


if __name__ == "__main__":
    main()