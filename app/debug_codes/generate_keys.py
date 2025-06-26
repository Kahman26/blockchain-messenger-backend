from app.utils.blockchain import generate_key_pair
priv, pub = generate_key_pair()

print("Public:")
print(pub)
print("Private:")
print(priv)