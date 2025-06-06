def logistic_map(seed: float, r: float, length: int) -> bytes:
    """
    Generate a chaotic keystream using the logistic map.
    Args:
        seed (float): Initial value between 0 and 1.
        r (float): Parameter (e.g. 3.9).
        length (int): Number of bytes to generate.
    Returns:
        bytes: A pseudorandom keystream of length `length`.
    """
    x = seed
    stream = []
    for _ in range(length):
        x = r * x * (1 - x)
        stream.append(int(x * 256) % 256)
    return bytes(stream)
