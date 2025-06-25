import replicate
import dotenv

dotenv.load_dotenv()

## Florence 2 Base
# input = {
#     "image": "https://aurus-chatbot.s3.us-east-1.amazonaws.com/swim_lane.png?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDYaCXVzLWVhc3QtMSJGMEQCIHQH1cBoEYeneYVwyWLPeYXtgoPC18D91vOU8EpfuvhqAiAzk9mJ1vOTpA3JbZvhM2BhNC5pp8CrAILbk7zfcQO%2BWiq5AwgvEAAaDDE4MzI5NTQyMTE5OCIMdYlwjYakohprHgfjKpYDJEkU2HEDnNzpgOl1g3GJkZKJ9hEvnHidUxsO5bvBGdTm%2BMO6wsG2t2pnCcKzzyWxQMtC2NBZj5Pk3iENzxbsdv%2Bb3jw%2Bop12FPFSmmuNkv%2Fv%2BdTg9lw24flF%2B%2FLtmAMN08ZCzQKErYM9co5B2cX%2B7WhsCWD7ozThI8tQYjB0W3fcPeLiF2t%2B%2BWeZ6h7hYCjoEc6hUm3BLiInxUYcrThVxIQfRO7KOnQVCIlCXGaCWNP9WWuDBF8bkd3tVJ8BgOf%2BEHvLI%2FkAfD7UomW%2F2VBAa7WT5y9iLeoGqFRN62AXHiDwPzcEwSyg0YI2HRWljo598IhXKUIohGxMoWjVnuH06pIWr3oxFC%2Bbl5F5DRtuy%2Bu4l%2FjyYtIvtRBtVg%2Byg1hhHt6TrIp8Hn7Uybg%2Fb0Scpsv%2FhQEMPVKvEhW6ffWxZwV1DHVcpHML%2FO%2B4Hxn1JRSN%2BS4w89yC2UbJU1x0ggfSLP4%2BT6yDhagEVHG0husjTaUTt50Y5WareRK5c9nCD%2FKRjUnXedPzoBY7KeEWJ5VTif3fKMWEMDCxy%2BrCBjrfAs7EmdgvSBJr%2FGrBaSgl8ilrXcX0On%2FhcKfstgiEAI72eB6xKNgl5vIhHSqPnzHrcIdKJCTwWPMTgTCza0G5Ai0bVBZQ69BzrXJSW3CCwdM%2FfC43voZZInVBDXxaOdIcxk%2BwhTbByG1MgV0F0KhJmhjOO3G5pvAea6jrXgW8gYTiQjvzxZRRjxncr0wnxSrtTkqK4lomtSM6XprZiecCGK818LP4DRjbK4QbLLIAYjupYjgd1iRK0qOaDWVm5AoK9bDcvSomMiH6XOIMNKVeQgb4pzry%2BFimAH0DQumS46MrWswSMxmZuKKsCNP1qaEzxGE0XG%2BIqxkxaEpBdn3z9o%2F8vyGF0PCN1XQDkMnVcU00pOHp3CIDE8F0nt8uUOG6WldjGVszRXe2vHiTa7qEr1lfih0WPnldT6M7ZUOqlralMBThRUWVeLLTLKlBrw4hLvNfGeFgPZ5ZKIZZbL1m9g%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIASVLKCFMHBEO5CXCZ%2F20250624%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250624T133536Z&X-Amz-Expires=36000&X-Amz-SignedHeaders=host&X-Amz-Signature=3da70e3be71fee9806e8a2137046fe00098501c74cb5d4e9ad6b668035674e3c",
#     "task_input": "More Detailed Caption"
# }

# output = replicate.run(
#     "lucataco/florence-2-base:c81609117f666d3a86b262447f80d41ac5158a76adb56893301843a23165eaf8",
#     input=input
# )
# print(output)

# ================================
## Llava 13b
# output = replicate.run(
#     "yorickvp/llava-13b:80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
#     input={
#         "image": "https://aurus-chatbot.s3.us-east-1.amazonaws.com/swim_lane.png?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDYaCXVzLWVhc3QtMSJGMEQCIHQH1cBoEYeneYVwyWLPeYXtgoPC18D91vOU8EpfuvhqAiAzk9mJ1vOTpA3JbZvhM2BhNC5pp8CrAILbk7zfcQO%2BWiq5AwgvEAAaDDE4MzI5NTQyMTE5OCIMdYlwjYakohprHgfjKpYDJEkU2HEDnNzpgOl1g3GJkZKJ9hEvnHidUxsO5bvBGdTm%2BMO6wsG2t2pnCcKzzyWxQMtC2NBZj5Pk3iENzxbsdv%2Bb3jw%2Bop12FPFSmmuNkv%2Fv%2BdTg9lw24flF%2B%2FLtmAMN08ZCzQKErYM9co5B2cX%2B7WhsCWD7ozThI8tQYjB0W3fcPeLiF2t%2B%2BWeZ6h7hYCjoEc6hUm3BLiInxUYcrThVxIQfRO7KOnQVCIlCXGaCWNP9WWuDBF8bkd3tVJ8BgOf%2BEHvLI%2FkAfD7UomW%2F2VBAa7WT5y9iLeoGqFRN62AXHiDwPzcEwSyg0YI2HRWljo598IhXKUIohGxMoWjVnuH06pIWr3oxFC%2Bbl5F5DRtuy%2Bu4l%2FjyYtIvtRBtVg%2Byg1hhHt6TrIp8Hn7Uybg%2Fb0Scpsv%2FhQEMPVKvEhW6ffWxZwV1DHVcpHML%2FO%2B4Hxn1JRSN%2BS4w89yC2UbJU1x0ggfSLP4%2BT6yDhagEVHG0husjTaUTt50Y5WareRK5c9nCD%2FKRjUnXedPzoBY7KeEWJ5VTif3fKMWEMDCxy%2BrCBjrfAs7EmdgvSBJr%2FGrBaSgl8ilrXcX0On%2FhcKfstgiEAI72eB6xKNgl5vIhHSqPnzHrcIdKJCTwWPMTgTCza0G5Ai0bVBZQ69BzrXJSW3CCwdM%2FfC43voZZInVBDXxaOdIcxk%2BwhTbByG1MgV0F0KhJmhjOO3G5pvAea6jrXgW8gYTiQjvzxZRRjxncr0wnxSrtTkqK4lomtSM6XprZiecCGK818LP4DRjbK4QbLLIAYjupYjgd1iRK0qOaDWVm5AoK9bD",
#         "top_p": 1,
#         "prompt": "Convert this flow diagramto a sequence of events and actions and describe properly what and how is the flow in proper steps",
#         "max_tokens": 1024,
#         "temperature": 0.3
#     }
# )
    
# # The yorickvp/llava-13b model can stream output as it's running.
# # The predict method returns an iterator, and you can iterate over that output.
# for item in output:
#     # https://replicate.com/yorickvp/llava-13b/api#output-schema
#     print(item, end="")

# ================================
# cogvlm

# output = replicate.run(
#     "cjwbw/cogvlm:a5092d718ea77a073e6d8f6969d5c0fb87d0ac7e4cdb7175427331e1798a34ed",
#     input={
#         "vqa": False,
#         "image": "https://aurus-chatbot.s3.us-east-1.amazonaws.com/swim_lane.png?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDYaCXVzLWVhc3QtMSJGMEQCIHQH1cBoEYeneYVwyWLPeYXtgoPC18D91vOU8EpfuvhqAiAzk9mJ1vOTpA3JbZvhM2BhNC5pp8CrAILbk7zfcQO%2BWiq5AwgvEAAaDDE4MzI5NTQyMTE5OCIMdYlwjYakohprHgfjKpYDJEkU2HEDnNzpgOl1g3GJkZKJ9hEvnHidUxsO5bvBGdTm%2BMO6wsG2t2pnCcKzzyWxQMtC2NBZj5Pk3iENzxbsdv%2Bb3jw%2Bop12FPFSmmuNkv%2Fv%2BdTg9lw24flF%2B%2FLtmAMN08ZCzQKErYM9co5B2cX%2B7WhsCWD7ozThI8tQYjB0W3fcPeLiF2t%2B%2BWeZ6h7hYCjoEc6hUm3BLiInxUYcrThVxIQfRO7KOnQVCIlCXGaCWNP9WWuDBF8bkd3tVJ8BgOf%2BEHvLI%2FkAfD7UomW%2F2VBAa7WT5y9iLeoGqFRN62AXHiDwPzcEwSyg0YI2HRWljo598IhXKUIohGxMoWjVnuH06pIWr3oxFC%2Bbl5F5DRtuy%2Bu4l%2FjyYtIvtRBtVg%2Byg1hhHt6TrIp8Hn7Uybg%2Fb0Scpsv%2FhQEMPVKvEhW6ffWxZwV1DHVcpHML%2FO%2B4Hxn1JRSN%2BS4w89yC2UbJU1x0ggfSLP4%2BT6yDhagEVHG0husjTaUTt50Y5WareRK5c9nCD%2FKRjUnXedPzoBY7KeEWJ5VTif3fKMWEMDCxy%2BrCBjrfAs7EmdgvSBJr%2FGrBaSgl8ilrXcX0On%2FhcKfstgiEAI72eB6xKNgl5vIhHSqPnzHrcIdKJCTwWPMTgTCza0G5Ai0bVBZQ69BzrXJSW3CCwdM%2FfC43voZZInVBDXxaOdIcxk%2BwhTbByG1MgV0F0KhJmhjOO3G5pvAea6jrXgW8gYTiQjvzxZRRjxncr0wnxSrtTkqK4lomtSM6XprZiecCGK818LP4DRjbK4QbLLIAYjupYjgd1iRK0qOaDWVm5AoK9bDcvSomMiH6XOIMNKVeQgb4pzry%2BFimAH0DQumS46MrWswSMxmZuKKsCNP1qaEzxGE0XG%2BIqxkxaEpBdn3z9o%2F8vyGF0PCN1XQDkMnVcU00pOHp3CIDE8F0nt8uUOG6WldjGVszRXe2vHiTa7qEr1lfih0WPnldT6M7ZUOqlralMBThRUWVeLLTLKlBrw4hLvNfGeFgPZ5ZKIZZbL1m9g%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIASVLKCFMHBEO5CXCZ%2F20250624%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250624T133536Z&X-Amz-Expires=36000&X-Amz-SignedHeaders=host&X-Amz-Signature=3da70e3be71fee9806e8a2137046fe00098501c74cb5d4e9ad6b668035674e3c",
#         "query": "Firstly tell me detailed sequence flow of events in the image from start to end and then describe it in detail"
#     }
# )
# print(output)

# ================================

# idefics3-8B-Llama3

output = replicate.run(
    "zsxkib/idefics3:b06f5f6b6249b27d0b00d1b794240e5641190d1582ad68c40ef53778459bb593",
    input={
        "text": '''Analyze this swimlane diagram:
            1. First, identify if swimlanes are horizontal (rows) or vertical (columns)
            2. List all swimlanes/departments based on the orientation
            3. For each swimlane, list activities in process order
            4. Describe the flow direction (left-to-right or top-to-bottom)''',
        "image": "https://aurus-chatbot.s3.us-east-1.amazonaws.com/swim_lane.png?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDYaCXVzLWVhc3QtMSJGMEQCIHQH1cBoEYeneYVwyWLPeYXtgoPC18D91vOU8EpfuvhqAiAzk9mJ1vOTpA3JbZvhM2BhNC5pp8CrAILbk7zfcQO%2BWiq5AwgvEAAaDDE4MzI5NTQyMTE5OCIMdYlwjYakohprHgfjKpYDJEkU2HEDnNzpgOl1g3GJkZKJ9hEvnHidUxsO5bvBGdTm%2BMO6wsG2t2pnCcKzzyWxQMtC2NBZj5Pk3iENzxbsdv%2Bb3jw%2Bop12FPFSmmuNkv%2Fv%2BdTg9lw24flF%2B%2FLtmAMN08ZCzQKErYM9co5B2cX%2B7WhsCWD7ozThI8tQYjB0W3fcPeLiF2t%2B%2BWeZ6h7hYCjoEc6hUm3BLiInxUYcrThVxIQfRO7KOnQVCIlCXGaCWNP9WWuDBF8bkd3tVJ8BgOf%2BEHvLI%2FkAfD7UomW%2F2VBAa7WT5y9iLeoGqFRN62AXHiDwPzcEwSyg0YI2HRWljo598IhXKUIohGxMoWjVnuH06pIWr3oxFC%2Bbl5F5DRtuy%2Bu4l%2FjyYtIvtRBtVg%2Byg1hhHt6TrIp8Hn7Uybg%2Fb0Scpsv%2FhQEMPVKvEhW6ffWxZwV1DHVcpHML%2FO%2B4Hxn1JRSN%2BS4w89yC2UbJU1x0ggfSLP4%2BT6yDhagEVHG0husjTaUTt50Y5WareRK5c9nCD%2FKRjUnXedPzoBY7KeEWJ5VTif3fKMWEMDCxy%2BrCBjrfAs7EmdgvSBJr%2FGrBaSgl8ilrXcX0On%2FhcKfstgiEAI72eB6xKNgl5vIhHSqPnzHrcIdKJCTwWPMTgTCza0G5Ai0bVBZQ69BzrXJSW3CCwdM%2FfC43voZZInVBDXxaOdIcxk%2BwhTbByG1MgV0F0KhJmhjOO3G5pvAea6jrX",
        "top_p": 0.8,
        "temperature": 0.4,
        "max_new_tokens": 512,
        "assistant_prefix": "Capture smallest details, arrows, and blocks in image flow diagram.",
        "decoding_strategy": "top-p-sampling",
        "repetition_penalty": 1.2
    }
)
print(output)