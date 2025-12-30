import datetime
import json

from sqlalchemy.orm import Session

from app.models import TermsTableModel

TERMS_CONTENT_V1 = {
    "ca": """<h2>TERMES I CONDICIONS D'ÚS</h2>
<p><strong>Darrera actualització:</strong> 22 de desembre de 2025</p>

<h3>1. Informació General</h3>
<p>Aquest lloc web és operat per [Nom de l'Empresa]. "
        "L'accés i l'ús d'aquesta pàgina atribueix la condició d'usuari "
        "i implica l'acceptació plena d'aquestes condicions.</p>

<h3>2. Propietat Intel·lectual</h3>
<p>Tots els continguts, textos, imatges i codi font són propietat de [Nom de l'Empresa] "
        "o de tercers amb autorització. "
        "Queda prohibida la seva reproducció sense permís previ.</p>

<h3>3. Limitació de Responsabilitat</h3>
<p>No ens fem responsables dels danys derivats d'interrupcions del servei, "
        "virus informàtics o un mal ús del contingut per part de l'usuari.</p>

<h3>4. Legislació Aplicable</h3>
<p>Aquests termes es regeixen per la normativa vigent i qualsevol litigi se sotmetrà als tribunals de [Ciutat].</p>""",
    "es": """<h2>TÉRMINOS Y CONDICIONES DE USO</h2>
<p><strong>Última actualización:</strong> 22 de diciembre de 2025</p>

<h3>1. Información General</h3>
<p>Este sitio web es operado por [Nombre de la Empresa]. "
        "El acceso y uso de esta página le atribuye la condición de usuario "
        "e implica la aceptación plena de estas condiciones.</p>

<h3>2. Propiedad Intelectual</h3>
<p>Todos los contenidos, textos, imágenes y código fuente son propiedad de [Nombre de la Empresa] "
        "o de terceros con autorización. "
        "Queda prohibida su reproducción sin permiso previo.</p>

<h3>3. Limitación de Responsabilidad</h3>
<p>No nos hacemos responsables de los daños derivados de interrupciones del servicio, "
        "virus informáticos o un mal uso del contenido por parte del usuario.</p>

<h3>4. Legislación Aplicable</h3>
<p>Estos términos se rigen por la normativa vigente y cualquier litigio "
        "se someterá a los tribunales de [Ciudad].</p>""",
    "en": """<h2>TERMS AND CONDITIONS</h2>
<p><strong>Last updated:</strong> December 22, 2025</p>

<h3>1. General Information</h3>
<p>This website is operated by [Company Name]. "
        "By accessing and using this site, you accept and agree to be bound "
        "by these terms and conditions.</p>

<h3>2. Intellectual Property</h3>
<p>All content, including text, images, and source code, is the property of [Company Name] "
        "or authorized third parties. "
        "Reproduction without prior permission is prohibited.</p>

<h3>3. Limitation of Liability</h3>
<p>We are not liable for damages resulting from service interruptions, "
        "computer viruses, or improper use of the content by the user.</p>

<h3>4. Governing Law</h3>
<p>These terms are governed by current legislation, and any disputes will be submitted to the courts of [City].</p>""",
}


def seed_terms(db: Session) -> TermsTableModel:
    """Creates default Terms and Conditions version with multilingual content."""

    existing_terms = db.query(TermsTableModel).filter_by(version="v1.0.0").first()
    if existing_terms:
        print(f"* Terms v1.0.0 already exists ({existing_terms.id})")
        return existing_terms

    print("Seeding Terms v1.0.0...")

    content_json = json.dumps(TERMS_CONTENT_V1)

    terms = TermsTableModel(version="v1.0.0", content=content_json, created_at=datetime.datetime.now(datetime.UTC))

    db.add(terms)
    db.commit()
    db.refresh(terms)

    print(f"* Created Terms v1.0.0 with ID: {terms.id}")
    return terms
