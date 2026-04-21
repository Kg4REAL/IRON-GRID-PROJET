  GNU nano 2.5.3                                              File: create_user.sh                                                                                               

#!/bin/bash

# Configuration
ADMIN_DN="cn=admin,dc=it,dc=local"
ADMIN_PW="admin"
LDIF_FILE="bulk_users.ldif"

# On vide le fichier au début
> $LDIF_FILE

# Liste des utilisateurs (Login:Nom:Prenom)
USERS=("moussa:Sarr:Moussa" "fatou:Diop:Fatou" "amadou:Ndiaye:Amadou")

i=2000
for user_data in "${USERS[@]}"; do
    IFS=":" read -r UID_NAME SN GIVENNAME <<< "$user_data"
    
    echo "dn: cn=$UID_NAME,ou=Users,dc=it,dc=local" >> $LDIF_FILE
    echo "objectClass: inetOrgPerson" >> $LDIF_FILE
    echo "objectClass: posixAccount" >> $LDIF_FILE
    echo "objectClass: shadowAccount" >> $LDIF_FILE
    echo "cn: $UID_NAME" >> $LDIF_FILE
    echo "sn: $SN" >> $LDIF_FILE
    echo "givenName: $GIVENNAME" >> $LDIF_FILE
    echo "uid: $UID_NAME" >> $LDIF_FILE
    echo "uidNumber: $i" >> $LDIF_FILE
    echo "gidNumber: 2000" >> $LDIF_FILE
    echo "homeDirectory: /home/$UID_NAME" >> $LDIF_FILE
    echo "loginShell: /bin/bash" >> $LDIF_FILE
    echo "userPassword: Password2026!" >> $LDIF_FILE
    echo "" >> $LDIF_FILE
    
    ((i++))
done

echo "[*] Injection des utilisateurs dans LDAP..."
ldapadd -x -D "$ADMIN_DN" -w "$ADMIN_PW" -f $LDIF_FILE

