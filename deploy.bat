@echo off
echo ================================
echo SUBINDO ALTERACOES PARA O ONLINE
echo ================================

git status

git add .

set /p msg=Digite a mensagem do commit: 

git commit -m "%msg%"

git push origin main

echo.
echo Deploy enviado para o GitHub/Railway.
echo Aguarde o Railway finalizar a publicacao.
echo.

pause