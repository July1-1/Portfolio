#!/bin/bash
# generate-cert.sh
set -e

KEYSTORE_PATH="src/main/resources/ssl/keystore.p12"
KEYSTORE_PASSWORD="password"
ALIAS="springboot"
VALIDITY_DAYS=3650

echo "Generando certificado SSL auto-firmado..."

if [ -f "$KEYSTORE_PATH" ]; then
    echo "El certificado ya existe en $KEYSTORE_PATH"
    exit 0
fi

keytool -genkeypair \
    -alias "$ALIAS" \
    -keyalg RSA \
    -keysize 4096 \
    -storetype PKCS12 \
    -keystore "$KEYSTORE_PATH" \
    -validity "$VALIDITY_DAYS" \
    -storepass "$KEYSTORE_PASSWORD" \
    -keypass "$KEYSTORE_PASSWORD" \
    -dname "CN=localhost, OU=Development, O=MiEmpresa, L=Ciudad, ST=Estado, C=ES" \
    -noprompt

chmod 644 "$KEYSTORE_PATH"
echo "Certificado generado exitosamente en $KEYSTORE_PATH"