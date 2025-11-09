# homelab
# outline of setup / repo frame work / bits of helpful code




## Git Crypt Setup
1. Install GPG and git-crypt:
# macOS:
brew install gpg git-crypt
2. Generate a GPG Key Pair (if you don't have one):
gpg --full-generate-key
3. Initialize git-crypt in your Repository:
git-crypt init
4. Add GPG Users to the Repository:
git-crypt add-gpg-user <GPG_KEY_ID_OR_EMAIL>
5. Configure .gitattributes for Encryption:
```
# Example: Encrypt all files ending with .key, has secret in the file name or in a 'secrets' directory
*.key filter=git-crypt diff=git-crypt
*secret* filter=git-crypt diff=git-crypt
secrets/** filter=git-crypt diff=git-crypt
```
6. Commit Changes and Push:
git add .gitattributes <encrypted_files>
git commit -m "Configure git-crypt and add encrypted files"
git push
7. Unlocking the Repository (for other users):
git crypt unlock
