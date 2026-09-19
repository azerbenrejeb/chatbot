import requests
from pathlib import Path
import urllib.parse
import re
import time

RAW_PDF_DIR = Path("c:/RSE Time/chatbot/rapport_non _annoteé")
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 31 redirection URLs from our search queries
URLS = [
    # SFBT
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFTe7vbqmowpl8Wrbw4RDdBQMmlMjz4KZVMyyFneuKGdREotkp_GCWQ3A598Pz24UL42RVtDWLWQuFyyiWUJo2zTuFc8XH7Mq1EsCc2_oGmuAJhZrJxdTIq6DWy6bw1fzZzM_vcNBhr2V-dBEb7Zs7783kD0uqU5cKl",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHn0eperxckUFEX2L1LAdj1ta6AscaQvUy2quoiyo_U1t3whojwo2OaRk437Um9UanOBE6CA888C-FIDxujaClRBMYHJgt_-PGl13pHfPl2lfHzovT3BQKYjZNbmsa8OC0gSZmZ0yP1h0aaI-k2JRAOnsEZtnKfJwtgYq45w7F7lWoXPSEJ",
    # Delice Holding
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH0k0f45GQLTf29ax9F7LRDrCMRzKmKbvx8nj1CyVNpCzEK68ipqgXKpDmTUIg1VO4sj2k6-IjN-Him-OBlwUCkrtUPpC2jaKn1JJ0YRVuPryNlEk_wR1GkqV0ECS6khbYGF5pUf0Z7jREQDljxC8FtDaGtL6iXZABQToemchI=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgFa89q5bNthpwIZh-nMOZEXSg3WwqQpPi_2rK4trF1wDdKjjtSKCM_KcRsPGK4ssyoTRcyH9pGNeLK4kw3Sl1NwBIDGSBn1FrxXa33P8od9C0pfZVVBLTw4iqMknEYlHrehVR0TZIKhJX078jp1WMzA1_i92Uo_6h29tvsdWqpgCgMEAZ7edQ_vaiDR9OSObIAro3dI4qvGeRmwjS3CxLqZ2D_T0I",
    # Sagemcom
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGFRqqBYuw-i8yAWhmONvZiwZ6H6GzcQOUFjsrDTgKyWyfH2Fi8KOQ3B0wFE-gLGpNhYnjr-gocbRerLwmjJaaN1uxL37YK2C85jO71VIRsoCBDIQ8IAQ88Da39HXLKdUP5CC7n3kC9RC_TbGPw-9CJu25aPdPYovN1LlHO_gysXx5d-2UW-Ek9kJkvIGM3W9SAEQ==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFdKTcwLNX2K-QkuOJU7_hWBIOW5Mvq3MjkUTEXTyF36wGrrQC8jU6tKILo34AvWBxOR52kP25Mos27kQq5apnVsfdX-aL5AoxL0kbHXs8rJdJQyfPW01jfzxGufOfHdTxfmZ7WEpFnVO9tT5oz4yY0acMcD1yy_DEagqBsr6ylkw==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQECP1uVvCHhea_Z4zjUwf4XHKWOG7we-Af8D3d09sKgtEEg9GTaVylFBkxYZAURmsV6Blv7c3KMeLLE9Olffr_yq41GB9vXoeKcl-f9voIHi-rp3WRgPfAYZvnllfsSZGrACo6uA3OaHegb85Vw4wDSu_88QN3wiyIg87PLys8=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEEj2MnnOkMTgJ2j7_r1_ocPxDrW6YEeN60IkHzk3uMwseEFeUXXNkcVtq9MOvUwzV8n6ioF5Qs2HXmZCCihNi07l3Vml_eJp_cvi_9D0JJ2Wou6vlWxX06c8NYhkWQNHhwBvYHA9-NLOuT2-7Tpp9VebUMDCDDZTRByDu6WidCqBBxofwOZeBosDnab1lvlndIsw==",
    # COLACEM
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFUlxtqdLjtRoAwDAqMcFvCqgXorl1rfKcdvK3Odv4XEtoBmxZGZetkEEBBLF1VeJmv-bJlkPuuAThc53XzwRZIaXYsfBztm2X137fAUPZ570KygsUYWPL1iP6esjq_WpOld49Dxlf4rR_MmWQl",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHCFP-95MGKt-NPn6HkL1cJtVmxIMxHiEGUq5UfNIKNsE1gYF5Hp4Qfb1ICUTk_IyrEIdiAnqn8gv1Loq3syI31juX3nLXxw4vEqoZbJJ0dJNz7yqCl52yZYAwTxF2dqEGGo16FklI8-cMuC3Kb",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFnRECoogSxqCnPomIZdPGOCuKS3sgo8hcPD8Ddt3p8XiY4nnMv3JVPSGhcJpQ84ktu99jRjcX6vJyGgHELzqMwz_3bNjG-XnBeQB6Vk8BX0-rvRWXGU9C_At1L_-Ql4vf4g5tBKLbxM7DTIlnxZY_6GbY=",
    # Tunisie Leasing
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFg7rkXTr3nXfezbIsOecaRg55tkDVIBqvpPlMzvj5GLE3pdnupKUNBxHNFaRthNmqDpnbd2CKeNFwXbYwJGmNCjGngEKqkiee4mpgwc2iQvxyGXeineWmadbQDlziYSGXiHZO_kVwEMv67HQ==",
    # Jost Group
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHPKvwXcJ8yr8j4C_uckD03O4OGcnYwDfFasMQMJ9q5vtu4dq0yq2U7dzQ1ZCcEQoEG8gTN6SdA9qBJfP0cYIodXCOeCMghrY6fA24j3BqksPh9iQQBbmq1lZamQR6bdO6IkcCOjUdevGNZJ8FevgGZzA==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHF8ORqsYq-UPqo3PBbXOMox8vrlbwmYFlJnGjBtgzsjtWz7Kc2cXK0Oq5izKgrtvX03nR2DbnH9ImK93tU6owEr6iWhP6pYTxkZXtWM9dw9qfBOqmkvRF8IhNMZ8usPv6t9VXEw8CXkGp-ud0ngmctKA==",
    # Engie Solutions
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG3tKQWGb6-ZuL6DTRF3aKpEFiyT2LsB4DMyxIB4zbuCEIcSf2bAs7eAX5VzhJ0WflDFjTPkl0jnCCooGjmhZrRP79lxD-SCuWWrOWjCxjDFkEyML3WWmNxqlC1Vb4eiW6nnkxZbOQeHw4jVBp3xQiMI_pL92fkZd1Z1TdVigAviH-UVyCs74aM81RUH0hnQ2Kx_IH6RgydmMMTc97UEaZIlQ==",
    # Spuerkeess
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGesM-X_ZS0CdOrIRAUQxUG-cODXUgL-7c8yhJZz6V3qNmEUsOBGt0VF5sDxRIEejz_jmf-vS4brPkrK7ivgKkvHRHcGd5mdxE8F01UYI2xGv7TdMzyEC8gymIv_xnIY42CAfQ3FXn070_5oxCtT1zsbh8ogdQgd8NsYiFATfId4nxfTlXsUtvAOqsukUjqDEKavoRqQ0e-8NXDzepjWG8HUnHi99wvnVTnGIxTO9iQETYj6lK2ZpD3Bw==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHMzCJ7jKISmwht5uRQWGypgzEwa0pUHZEum5W9mCZDHtEq0p9Q1NChCtFBbtXnjwsoutzYp6wj4KzwHOhOvNhe8DhACoiiQg7iyKIyWB0jQubH4b2b7wj2DXotoKX5mlYMjnPtulWneCe1oGTOk3Tkqd2VQJag7SchGmJwgZ4mziU9VRqLyDT8d4mkSecSUyzD29OKsTQXOK1zZ-3F0h2xxt_XjaHIq8-MMJYPgqQAZG6JuPHNXwOU1Q==",
    # Comar Assurances
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFJiRUWnJ05RwW-dsoqt8prerVzQ6ze_6f9UtfjGsTFv-AhqA1mNlql0CrZ-7gPblhnavdOaTCxEJbGe45OubQsJwJY8LPe33winjXBUaWRyOli8k-qwbvKibVq6KiEjfIsNxRngYs7WlTzHImhJd_0-mMja9sf1nTIXh7bH2tB",
    # Bonduelle
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGY_5prKSpwxO300zdH1TriAvhtjrs3lvfZCgzs0lFOG26FkGRvhrMaMm_w_spLyIEFEc3ZuWtPGo3FnaQrbMZtSfpBzgQI2emoGnG0lZbHQY97BObOIm8brLkYqNoaneRwxJUstJzBsp5yJNdVbjtmv2UoF9z4_DSar_tRm8K1uMIGVMI7GEOX",
    # Square Management
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgUuLOiMzoCcbfx1UjL0o9HLs-q3FVTJmkiiwGWm7IDfiOQi63TUrgV9ehh3jwnEDo5Cmmrf1n3sabCcRFp7o8nJf5RLss45qi6Nnq-fp3jKKNo8nQ7mHtmks7oiy2enMElDdfqIZ-ux35tP_76L2Aq_S5Ug7ufJjBPDbiLCuBoYbdQxIkyu8fARsm1AGwUja2umqTlmm-Cg==",
    # Blard Assainissement
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG3cj4Yjr2dZXVRudFVDmG5C14BVqsSDaPEJ03EQvg-na6OE2Omgb8Y59rLeXlOqFLmOteibhajDid4J0wnQC8yO0GGvdOo7wC2t763SaSKHYRcCOvdYv2put510K8IwdFsrngALIfGZ8Fvz0zcM-FO9XrdBrymMCBPM7l8FiJeE1g6_P59apsCnpxS5oMy",
    # Cerelia Group
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHyPilImKdt11gumgoZAAWH8kwq6oRXI_lXpg09lIpfrW649RpM5csFrJ78qWN_aVGvQJ0gNy2mUGlQTeowILsW-Yagb_NCwTNZSWtKc0jomr9cCaGTUiR7ky9sQuhqRlsEPUBvnAPJAA_MzNIIJKK4ffHF4Lmy6vwtT6-DsITN",
    # DPD France
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgW7CkmsXR2lIBlMT2ylPoWZpA1De2RO0z4H-_V2sawsHM3ePQXtI3acXejMVFpcDuNFkYe1z_BSSy20JYtWc4Z5OphtNFU0-RFZ8gRj6HWMWJyEEUjVxU7zE11fmeXDiWQ4s9vG3f4Uqd1xDHmUvPCkmytTy9ND1RtdmOoMPZ4kIH",
    # Becouze Talents
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-_Ir7U3egdwOt8aeiGSMaZlaqw2XUK7s_EsBpVSS5bYeA_FG9TUN_ueInm3JE6NQi-F_sjmjgTAiFGJkRgb1WQpf3DZlpBMOo_M5VqzfsHlgnDb7RxBwsRW0nOAH-YI4Yrpn3xZkFRQbyE3O0XutyJw7GVkFSEq9vZq0j_rfYRpqtDdVdkRsb",
    # BWT France
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFcjsW4Nc7IssCES9yQY7EZHvmHE3Lg2hHMzwgUyGDMAt0uJyjrgM8mzKxQNdG6AOdtJVtH9DWcbmaCPPANHgvD4_FDluG4s_CDDZNgqEDht1k881S7FC3uK_NaTLioEY_JvND9XvXQ2Xk5azHJYMPsLZK9Im2whWN9FAMsSVGnhXOF7HPLW0qVeTOyuW5K4TEForkwWI3yNo_y6woFgqTNXpxAJME=",
    # Formes & Sculptures
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHDX8JV8BC0UDOr13YJLyyxa2MuNnyPE6GyKyC0NLGuxgMs2qH_ikJy9bXe6AbiFGK9so8CA8p_Md0nWU3ma6YyEtAqHKBUrflhvZb5PhYVselYLO7FV2SEJHFdx8XPZGm6OzGUarwMPpyBj1aBzzgKoEtw4miT-y7ocUeA9YSWQ-6InTLTYs4=",
    # TMM Tunisie
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGXESuDhNZbdbUl6HcN_zbAT1R249NahUcIdRa09Gi6NEcD-2EqzPt4wTz3P_Loo0qvP2IAKrrg3NabT6GyFzLtBIfngjQdSfXlr8spDbixdAZX4X4XKxc1z0Xwesb7zxT_aFHZP1ND_600PALrPXsqeYtHtgxvXnPSdAqUKKkcAkOLRTQkD88j",
    # Ferrero
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH53o-pYEhOpobT0pTs850Y21ky_H7QvvB_g_mRKDSX6e0WqHaAOgDOsJWxojw6wB6FkLDRyHD377ww0O4LpPdv3J7eZmzzJ-owjq2sH1lDcwgAZnYH1vjlURn-Ibq0QsE-WXoGK5wE62uQboU20eM_uhtx-b_QbFWuix2lSvRGiW0aNNl6xQWdCnrZ-82sfovERA==",
    # Grant Thornton
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG0XbbgrlRPfqUpROJc2aJfuvM9sawgePktmP4S9IPYTrLMIXZqZ378WKOW2MdF_R8z5dS_5njfc7mAyv7bk6p2J9K3-92_odCyW_bv18wWUuX6OQjoFogzo1xv1eNAGE7hgIegMyRw-aJt9FN3k1D1UwZSttbeeHBw_vKXsoMWqfl4ToWl55yrTHJXRF61TWsZrQ3s7vMSJLey0n0ip9FrzdAhJdHt5_HB9W_3M6xEde6Uh2pNs9CRLUlw",
    # Tarkett Group
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZ6zZF--8EzE2cmazZdZgtEFF4Z7ZjF-JguDnzb2HTYXa08xB8Fk95cnRpCm3Yxomah-XXU5H0kNMs1A1VcRLviYn9LKfFOoU0qSxmA4Tc2_kHXImaPZGD-1yRdpCPmjyIatOCc-BNyK80K7XiSnYUeo9CULvsqSUrESbvbCSLaGprvkRx-YEcqHk4SMA9K76xig==",
    # Clayens
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG46KmYv11u-4vzwC8yr7_M5B8VlSo-WJANcSzaYtzZSb9OWltP3k8-JJb0Cbu159ePwOEVwLwQvmOXFI87OdzqBszJ68Q9kmB6D3ZL-g28pgTWxpoEI_XPmiL20U_4UIeQ1d_DC_ihZ_zeqUdgF50BcUOs6jvTA_jtaTArPq2SwYNG3oE_6vDavovw6ajzQm_oAwv0F9nC1l5isDUd",
    # Seine-et-Marne
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFV4pA1jMolRxRcaUQsDSKR_meLV6XA_EFTYbddZvZJCYpUVVGVb6iDrNnRnEilSCbizBDRK7BY2mh0MOUVe3-5lRQOb3R_ylbJJT8A5zfQ8U_TjJNBCwXO84Hr9ntCptKm__pnnJZ7qD19MkzrSmzqiSCbSY2eTHFjkgpxMHqaxEQvI0Xr1QtIvPzh4KacuX_vrvYWP2Q=",
    # BNP PF
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGLcDhAfgU3Poq3KewNXZ0yXUfSyPUHsh7s4Iyeqc9DUFlXl6utC3aVBVnftwV5i9WFtp7u5C06TXrujQwX2iRQ7wJoWLvunMHIrytez13w83VB-U4_iEM9thQQ-dwg4afT256yZIpueSE75UncSawOvpp5FgRj3hgkSBuaGH7H8hjpulNSumcXye1m1d66S2cqhz5J6WID_R-4okp65BdaN_8=",
    # Sfil
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHZsGfP_Wvs-zREVsy5-1drLIeryhbWOasoBanfXI1hcEDLRrFcbW_p57XhK0q4-Yvsf7xFRVppaCTC5jyHU5R93vdj_6FNu2ccQPGdYl0fYuJ7a4wbAAK4CtMk84eOPGwXQwpxxX9i2HkAbiSKnTTc2Q_0dUfXsNUFrJzNAh9Jyg==",
    # Bontaz
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG_hamNJWYOzmKrE0rtMNuLS1TehktwNKoUHUrD0bNnikySY_ypOqs0PMz3O3-CXCk5TuC8acCo_E71mlszEY8-NmZhyv7wph1ClfjJKjCPh4e8SlpMYDiCtfLQbXczHmC964vgUsvVGF6JKDszb0SKjwQXwppS5mPpZq9x5YYMJ4yk4OLNebEc32U4Cc5E4kf9qiY7yBY_qDFl",
    # Italgraniti
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFhi9sghkIxU9PWUNFOk0ofmB5sVWMaPDRln_gwp_OPUOWlb9zkA7cShGbJJGnct3RfSPEhrLqJObl9I8AoTJmVXBSAzNUFRZHGfGxp9yWSYoQaJ7kBXJ37I7LBU_6Qf7YON552BJ-ka0Jl6PYqHuXPI58W-wzzx4BNPgqr8XqMj39CkC8WEjBlOJBhVOxl3XbY94QJ9U5S4Kzr4Fk5D20Mh0MRi7yhU1U=",
    # Aviapartner
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEXlb0PeFiDM6BZKZYC3v9OdF23e-ZHIDg9BvWM0UxfR-3ZbgfFSna_fCxEsAPF4qB2LVsqD9x4mV7eug4KX67RLojO7e90h46BoebeYIRiNuF3WBYUQZKbn1aI8emDFueMLL7EQt1xP-dKfbjo1ewMQtl8jpL3r1sBwyQyd-_NGXUGteuzEBo0snNdwdTS5F73ozBSUNtjn0__rCqa0zzVq-M0R-hv-Q==",
    # MBDA
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-dJ2WhfTy7bXjr4HUE_6-7enfhyyq1cAWRiSieSBfX-w3l8SviYh4zmqMMQIVRFDNsp5-L1eWbExcSGWS8Ov93Tm9B2sSu2DGoRf2QXmswBzQ6RU9KvXSuwhysUxx4KEDzu2Ww7R3ZTuxDCJRq2-qK6CFEuqR5P-6_aLbcDE-OsG9nAsK82kPxcU5Cqkm2NeAaGOOtMJa",
    # Systra
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGvL-V74WIaFzxyzcb41OoO9MRIwaOBJBzqEbw5WUXuQLUWhEf5AkwSeqdz4qC6ahC7mKytjJWsbrf-iGxWWx69wdeBv-ddZlN2ALzN1u3mxdW6t0M1kreu_ey4ipNpdiQHnrAJ3tiVCZfCuTPdyZhhM2w4tAY7gA==",
    # Delaware
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHjfiy0eJ44zZfI9Wn1czx0HGGLJYxXjbDH9ASR0snbPTw5fHHl_09ivEylL5fmpmAWiFl5s7F-ir93ULvFDfkzPnJXEHT4dd442HGERmiWX4YhG2GBfxtOItRQTusHlOMZPiaAL0fHyeXnZRuKDaNnYSPml_7uXaRG5tmLjNEostMMm6ZXPorzjkqoviT7wNmomAS41YKEbA==",
    # AXA
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEInSuX1V0fwxDRdTy67uhcg620PngOe4d2LbD2DHaf2equA_wQM3ybMefyifhqzl0uNCSg9LgZpqWOZNdt13AsCn80iubOUzN778XuxxuSbqmov50UgL7wgjOUyNt28wR8zn82jRah1k740aSpuVX9zRSzznk3Dpk=",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCXa6cTMFIdAeloaobDFvUGdlxqSnRqXgB3u2NpktkeDFke_cA8jx1cqoK__bRvXJZMG0TEV8nu6BWfyVb9P-zZOrYopAn1sKqJNOnPvbZhzKcqdVGfN-SL4UIgowI7DwaYzAa-bnQVV4SYGZ1WreUt9t65NTTWm0=",
    # Sanofi
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHOEmYv1Q8zJHhgt1kvrktqr2oTXE3-RcrSPNPRyRxVT54LTfZK6juiPA-Y2ZjqMLcdje0XhehxfxHXdQ9Fq6bH8qPf74vxwdWLjTTqsDeKSOETf5sIAIMxoI0QyPqO5EfoBbIogeInDdHGe0vw8Gt9ED9qtr5p4WL9awuub9mmVPs0rTtWDj8B4A4t6u4KhtWGnSwkYtVe2Ay8gnx-lQLFqJZxth1rqenyndLBqA==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEtBABMW6fGTuqsWIQ6mqIksYAZBC6LD1bxeuTbYQuGBXTp28KjXL6plaxLod85SVkrpqxgChBCm_6DaFp7BIW6JW6kuYz5xJ2Lrw3GPbHCNq0miiXAkfeiVffOU9XjhPOcJtLuC7Yr_vURlPCj1aNw3wIeiEFUJzkHMg-x1aBrQofYNShxqB36nlgYuh3RVNwOkT7Eebcu-w==",
    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3Vutnkat9JAZvGXeAnKBlBkC3HhHIXqA7xU9hQlLwMPS3ciIaqn2gRTqV-q0B63EteezLYrtl5-Gsshmvpa0zWg9v4zkS0Nu9BaD0c6umy4EVZjRRFmOEZRLmtCbu31QcVmXhG1lQAiR22OVM6vu0CN7V8yVDL7yqTpe5PDqXSDDLJJLgeQLlDPq-SCEfbjymktUiW7Ds2NXW-bOr_CP_Tcss70wwttXfODW1",
]

def download_pdf(url, dest_dir, idx):
    try:
        print(f"[{idx+1}/{len(URLS)}] Résolution de la redirection pour {url[:100]}...")
        # Suivre les redirections, timeout 12s
        r = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code != 200:
            print(f"  -> [ERR] HTTP Status: {r.status_code}")
            return False
            
        final_url = r.url
        content_type = r.headers.get("Content-Type", "")
        print(f"  -> Résolu à : {final_url} (Type : {content_type})")
        
        if "application/pdf" not in content_type and not final_url.lower().endswith(".pdf"):
            print("  -> [ERR] Le fichier n'est pas un PDF")
            return False
            
        # Extraire le nom du fichier
        filename = Path(urllib.parse.unquote(final_url.split("/")[-1].split("?")[0])).name
        filename = re.sub(r"[^\w\-_.]", "_", filename)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            
        dest_path = dest_dir / filename
        
        # Écrire
        with open(dest_path, "wb") as f:
            f.write(r.content)
            
        print(f"  -> [SUCCÈS] Sauvegardé sous {filename} ({len(r.content)} octets)")
        return True
        
    except Exception as e:
        print(f"  -> [ERR] {e}")
        return False

def main():
    success_count = 0
    start_time = time.time()
    for idx, url in enumerate(URLS):
        success = download_pdf(url, RAW_PDF_DIR, idx)
        if success:
            success_count += 1
        # Éviter de surcharger
        time.sleep(1)
        
    print(f"\nTéléchargement terminé en {time.time() - start_time:.1f}s.")
    print(f"{success_count} / {len(URLS)} rapports PDF téléchargés avec succès dans {RAW_PDF_DIR}")

if __name__ == "__main__":
    main()
