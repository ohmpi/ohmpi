pyreverse ohmpi -p uml_ohmpi
dot -Tpng classes_uml_ohmpi.dot -O
dot -Tpng packages_uml_ohmpi.dot -O
mv classes_uml_ohmpi.dot uml_diagrams/
mv classes_uml_ohmpi.dot.png uml_diagrams/
mv packages_uml_ohmpi.dot uml_diagrams/
mv packages_uml_ohmpi.dot.png uml_diagrams/


