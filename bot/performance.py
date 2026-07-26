import time


class Timer:

    def __enter__(self):

        self.start = time.time()

        return self

    def __exit__(self, *args):

        print(

            f"Completed in {time.time()-self.start:.2f}s"

        )
