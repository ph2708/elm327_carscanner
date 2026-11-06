"""
Gerenciador de Perfis de Veículos e Persistência do Histórico de Diagnósticos.
Armazena a garagem de carros cadastrados, placas e relatórios de passagens em arquivo local.
"""

import os
import json
import time

DATABASE_PATH = os.path.join(os.path.expanduser("~"), ".autoscan_vehicles_db.json")

class GarageProfileManager:
    @staticmethod
    def load_database():
        if os.path.exists(DATABASE_PATH):
            try:
                with open(DATABASE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "selected_plate": "BRA2E19",
            "vehicles": {
                "BRA2E19": {
                    "plate": "BRA2E19",
                    "model_key": "GM_FAMILIA_1_10_14",
                    "model_name": "Chevrolet Onix / Prisma / Celta / Corsa 1.0 e 1.4 8V SPE/4",
                    "year": "2019",
                    "km": 68000,
                    "customer_name": "Cliente Oficina",
                    "created_at": time.strftime("%d/%m/%Y"),
                    "history": []
                },
                "ABC-1234": {
                    "plate": "ABC-1234",
                    "model_key": "FORD_SIGMA_15_16",
                    "model_name": "Ford New Fiesta / Ka 1.5 e 1.6 16V Sigma Flex",
                    "year": "2015",
                    "km": 85000,
                    "customer_name": "Proprietário Atual",
                    "created_at": time.strftime("%d/%m/%Y"),
                    "history": []
                },
                "BYD-0E24": {
                    "plate": "BYD-0E24",
                    "model_key": "BYD_DOLPHIN_MINI_EV",
                    "model_name": "BYD Dolphin / Dolphin Mini / Yuan Plus 100% Elétrico (EV)",
                    "year": "2024",
                    "km": 15000,
                    "customer_name": "Cliente Elétrico",
                    "created_at": time.strftime("%d/%m/%Y"),
                    "history": []
                },
                "GOL-1600": {
                    "plate": "GOL-1600",
                    "model_key": "VW_EA111_10_16",
                    "model_name": "Volkswagen Gol / Fox / Voyage / Saveiro 1.0 e 1.6 8V EA111",
                    "year": "2014",
                    "km": 112000,
                    "customer_name": "Frota Oficina",
                    "created_at": time.strftime("%d/%m/%Y"),
                    "history": []
                }
            }
        }

    @staticmethod
    def save_database(data):
        try:
            with open(DATABASE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar banco de veículos: {e}")

    @staticmethod
    def delete_vehicle(plate):
        db = GarageProfileManager.load_database()
        plate = plate.upper().strip()
        if plate in db.get("vehicles", {}):
            del db["vehicles"][plate]
            if db.get("selected_plate") == plate:
                rem = list(db["vehicles"].keys())
                db["selected_plate"] = rem[0] if rem else ""
            GarageProfileManager.save_database(db)
            return True
        return False

    @staticmethod
    def get_vehicle(plate):
        db = GarageProfileManager.load_database()
        return db.get("vehicles", {}).get(plate.upper().strip())

    @staticmethod
    def get_all_vehicles():
        db = GarageProfileManager.load_database()
        return db.get("vehicles", {})

    @staticmethod
    def save_or_update_vehicle(plate, model_key, model_name, year, km, customer=""):
        db = GarageProfileManager.load_database()
        plate = plate.upper().strip()
        if not plate:
            plate = "SEM-PLACA"

        if plate not in db["vehicles"]:
            db["vehicles"][plate] = {
                "plate": plate,
                "model_key": model_key,
                "model_name": model_name,
                "year": year,
                "km": km,
                "customer_name": customer,
                "created_at": time.strftime("%d/%m/%Y"),
                "history": []
            }
        else:
            db["vehicles"][plate]["model_key"] = model_key
            db["vehicles"][plate]["model_name"] = model_name
            db["vehicles"][plate]["year"] = year
            db["vehicles"][plate]["km"] = km
            if customer:
                db["vehicles"][plate]["customer_name"] = customer

        db["selected_plate"] = plate
        GarageProfileManager.save_database(db)
        return db["vehicles"][plate]

    @staticmethod
    def add_history_entry(plate, analysis_result, ai_report=""):
        db = GarageProfileManager.load_database()
        plate = plate.upper().strip()
        if plate in db["vehicles"]:
            entry = {
                "date": time.strftime("%d/%m/%Y %H:%M"),
                "score": analysis_result.get("health_score", 100),
                "duration_sec": analysis_result.get("duration_sec", 0),
                "metrics": analysis_result.get("metrics", {}),
                "anomalies_count": len(analysis_result.get("anomalies", [])),
                "anomalies": analysis_result.get("anomalies", []),
                "ai_report": ai_report
            }
            db["vehicles"][plate]["history"].append(entry)
            GarageProfileManager.save_database(db)
            return True
        return False

