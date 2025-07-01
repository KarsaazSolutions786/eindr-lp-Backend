#!/usr/bin/env python3
"""
Sample Data Setup Script for Multi-Language Label System
This script creates sample languages, label groups, label codes, and translations
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database_psycopg import get_database_session, create_tables
from app.models import (
    LanguageCreate, LabelGroupCreate, LabelCodeCreate, LanguageLabelCreate
)
from app.services import (
    LanguageService, LabelGroupService, LabelCodeService, LanguageLabelService
)

async def setup_sample_data():
    """Set up sample data for the multi-language label system"""
    
    print("🚀 Setting up sample data for Multi-Language Label System...")
    
    # Ensure tables are created
    await create_tables()
    
    # Get database session
    async for db in get_database_session():
        try:
            # Step 1: Create Languages
            print("📝 Creating languages...")
            languages = [
                LanguageCreate(name="English", code="en", is_active=True),
                LanguageCreate(name="Spanish", code="es", is_active=True),
                LanguageCreate(name="French", code="fr", is_active=True),
                LanguageCreate(name="German", code="de", is_active=True),
                LanguageCreate(name="Portuguese", code="pt", is_active=True),
            ]
            
            created_languages = {}
            for lang_data in languages:
                try:
                    language = await LanguageService.create_language(lang_data, db)
                    created_languages[language.code] = language
                    print(f"  ✅ Created language: {language.name} ({language.code})")
                except ValueError as e:
                    print(f"  ⚠️  Language {lang_data.name} already exists")
                    # Get existing language
                    existing_languages = await LanguageService.get_all_languages(db)
                    for lang in existing_languages:
                        if lang.code == lang_data.code:
                            created_languages[lang.code] = lang
                            break
            
            # Step 2: Create Label Groups
            print("\n📁 Creating label groups...")
            label_groups = [
                LabelGroupCreate(name="home", description="Homepage labels"),
                LabelGroupCreate(name="navigation", description="Navigation menu labels"),
                LabelGroupCreate(name="forms", description="Form labels and buttons"),
                LabelGroupCreate(name="errors", description="Error messages"),
                LabelGroupCreate(name="common", description="Common UI elements"),
            ]
            
            created_groups = {}
            for group_data in label_groups:
                try:
                    group = await LabelGroupService.create_label_group(group_data, db)
                    created_groups[group.name] = group
                    print(f"  ✅ Created label group: {group.name}")
                except ValueError as e:
                    print(f"  ⚠️  Label group {group_data.name} already exists")
                    # Get existing group
                    existing_groups = await LabelGroupService.get_all_label_groups(db)
                    for grp in existing_groups:
                        if grp.name == group_data.name:
                            created_groups[grp.name] = grp
                            break
            
            # Step 3: Create Label Codes
            print("\n🏷️  Creating label codes...")
            label_codes_data = [
                # Home page
                {"code": "text_welcome", "description": "Welcome message", "group": "home"},
                {"code": "text_subtitle", "description": "Homepage subtitle", "group": "home"},
                {"code": "btn_get_started", "description": "Get started button", "group": "home"},
                {"code": "text_features", "description": "Features section title", "group": "home"},
                
                # Navigation
                {"code": "menu_home", "description": "Home menu item", "group": "navigation"},
                {"code": "menu_about", "description": "About menu item", "group": "navigation"},
                {"code": "menu_contact", "description": "Contact menu item", "group": "navigation"},
                {"code": "menu_services", "description": "Services menu item", "group": "navigation"},
                
                # Forms
                {"code": "label_email", "description": "Email field label", "group": "forms"},
                {"code": "label_name", "description": "Name field label", "group": "forms"},
                {"code": "btn_submit", "description": "Submit button", "group": "forms"},
                {"code": "btn_cancel", "description": "Cancel button", "group": "forms"},
                
                # Errors
                {"code": "error_required", "description": "Required field error", "group": "errors"},
                {"code": "error_email_invalid", "description": "Invalid email error", "group": "errors"},
                {"code": "error_server", "description": "Server error message", "group": "errors"},
                
                # Common
                {"code": "text_loading", "description": "Loading text", "group": "common"},
                {"code": "text_save", "description": "Save text", "group": "common"},
                {"code": "text_close", "description": "Close text", "group": "common"},
            ]
            
            created_codes = {}
            for code_data in label_codes_data:
                group_id = created_groups[code_data["group"]].id
                label_code_create = LabelCodeCreate(
                    code=code_data["code"],
                    description=code_data["description"],
                    label_group_id=group_id
                )
                
                try:
                    code = await LabelCodeService.create_label_code(label_code_create, db)
                    created_codes[code.code] = code
                    print(f"  ✅ Created label code: {code.code} (group: {code_data['group']})")
                except ValueError as e:
                    print(f"  ⚠️  Label code {code_data['code']} already exists")
                    # Get existing code
                    existing_codes = await LabelCodeService.get_label_codes_by_group(group_id, db)
                    for existing_code in existing_codes:
                        if existing_code.code == code_data["code"]:
                            created_codes[existing_code.code] = existing_code
                            break
            
            # Step 4: Create Language Labels (Translations)
            print("\n🌍 Creating language labels (translations)...")
            
            # English translations
            english_translations = {
                "text_welcome": "Welcome to our website!",
                "text_subtitle": "Your journey starts here",
                "btn_get_started": "Get Started",
                "text_features": "Features",
                "menu_home": "Home",
                "menu_about": "About",
                "menu_contact": "Contact",
                "menu_services": "Services",
                "label_email": "Email Address",
                "label_name": "Full Name",
                "btn_submit": "Submit",
                "btn_cancel": "Cancel",
                "error_required": "This field is required",
                "error_email_invalid": "Please enter a valid email address",
                "error_server": "An error occurred. Please try again later.",
                "text_loading": "Loading...",
                "text_save": "Save",
                "text_close": "Close",
            }
            
            # Spanish translations
            spanish_translations = {
                "text_welcome": "¡Bienvenido a nuestro sitio web!",
                "text_subtitle": "Tu viaje comienza aquí",
                "btn_get_started": "Empezar",
                "text_features": "Características",
                "menu_home": "Inicio",
                "menu_about": "Acerca de",
                "menu_contact": "Contacto",
                "menu_services": "Servicios",
                "label_email": "Correo Electrónico",
                "label_name": "Nombre Completo",
                "btn_submit": "Enviar",
                "btn_cancel": "Cancelar",
                "error_required": "Este campo es obligatorio",
                "error_email_invalid": "Por favor ingrese un correo electrónico válido",
                "error_server": "Ocurrió un error. Por favor intente de nuevo más tarde.",
                "text_loading": "Cargando...",
                "text_save": "Guardar",
                "text_close": "Cerrar",
            }
            
            # French translations
            french_translations = {
                "text_welcome": "Bienvenue sur notre site web!",
                "text_subtitle": "Votre voyage commence ici",
                "btn_get_started": "Commencer",
                "text_features": "Fonctionnalités",
                "menu_home": "Accueil",
                "menu_about": "À propos",
                "menu_contact": "Contact",
                "menu_services": "Services",
                "label_email": "Adresse Email",
                "label_name": "Nom Complet",
                "btn_submit": "Soumettre",
                "btn_cancel": "Annuler",
                "error_required": "Ce champ est obligatoire",
                "error_email_invalid": "Veuillez saisir une adresse email valide",
                "error_server": "Une erreur s'est produite. Veuillez réessayer plus tard.",
                "text_loading": "Chargement...",
                "text_save": "Sauvegarder",
                "text_close": "Fermer",
            }
            
            # Create translations for each language
            all_translations = [
                ("en", english_translations),
                ("es", spanish_translations),
                ("fr", french_translations)
            ]
            
            for lang_code, translations in all_translations:
                language = created_languages[lang_code]
                print(f"\n  📝 Creating {language.name} translations...")
                
                for code_key, translation_text in translations.items():
                    if code_key in created_codes:
                        label_code = created_codes[code_key]
                        
                        label_data = LanguageLabelCreate(
                            language_id=language.id,
                            label_id=label_code.id,
                            label_text=translation_text
                        )
                        
                        try:
                            await LanguageLabelService.create_language_label(label_data, db)
                            print(f"    ✅ {code_key}: {translation_text}")
                        except ValueError as e:
                            print(f"    ⚠️  Translation for {code_key} already exists")
            
            print(f"\n🎉 Sample data setup completed successfully!")
            print(f"📊 Summary:")
            print(f"   - Languages: {len(created_languages)}")
            print(f"   - Label Groups: {len(created_groups)}")
            print(f"   - Label Codes: {len(created_codes)}")
            print(f"   - Translations: {len(all_translations) * len(english_translations)}")
            
            print(f"\n🔗 API Endpoints to try:")
            print(f"   - GET /api/languages - List all languages")
            print(f"   - GET /api/languages/1/labels - Get English labels")
            print(f"   - GET /api/languages/2/labels - Get Spanish labels")
            print(f"   - GET /api/label-groups - List all label groups")
            print(f"   - POST /api/labels/validate - Validate before inserting new labels")
            
        except Exception as e:
            print(f"❌ Error setting up sample data: {e}")
            raise
        
        finally:
            await db.close()


async def main():
    """Main function"""
    print("🏗️  Multi-Language Label System Setup")
    print("=" * 50)
    
    try:
        await setup_sample_data()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 