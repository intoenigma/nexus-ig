import os

from dotenv import load_dotenv

from nexus_ig.core import console
from nexus_ig.core.config import load_config
from nexus_ig.instagram.groups import is_group_thread
from nexus_ig.services.provider import InstagramProvider
from nexus_ig.core.storage import Storage



def main():
    load_dotenv()
    config = load_config()
    storage = Storage(config.database_file)

    console.memory_screen()

    from nexus_ig.instagram.login import login_client
    cl, my_pk, my_username = login_client(config)
    if not cl:
        console.error("Login failed. Run 'python login.py' to authenticate.")
        storage.close()
        return

    console.status("FETCH", "Reading recent threads")
    threads = cl.direct_threads(amount=50)

    count = 0
    for thread in threads:
        if is_group_thread(thread) and not storage.has_greeted(thread.pk):
            storage.mark_greeted(thread.pk, thread.thread_title or "")
            storage.upsert_group(thread.pk, thread.thread_title or "")
            count += 1
            console.success(f"Marked seen: {thread.thread_title or thread.pk}")

    storage.close()
    console.section("DONE")
    console.row("Groups added", count)


if __name__ == "__main__":
    main()
