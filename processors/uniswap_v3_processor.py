from typing import Dict, Any, List, Tuple
from .base_processor import BaseProcessor
from database.models import BaseTransaction, SwapEvent, MintEvent, CollectEvent, BurnEvent, FlashEvent, Token
import logging

logger = logging.getLogger(__name__)


class UniswapV3Processor(BaseProcessor):
    def __init__(self):
        super().__init__('uniswap_v3')
        self.logger.info("Initialized UniswapV3Processor...")
    
    def process_bulk_responses(self, response_data: Dict[str, Any]) -> List[Dict[str, list]]:
        self.logger.debug(f"Processing bulk responses on {self.dex_id} with {len(response_data.get('data', {}).get('transactions', []))} transactions")
        # Initialize results for each event type
        results = [[],[],[],[],[]]
        try:
            # Iterate through each transaction in the response
            for transaction_data in response_data['data']['transactions']:
                events = self.process_response(transaction_data)
                
                # Append events to results
                results[0].extend(events['swaps']) # Add swaps to results
                results[1].extend(events['mints']) # Add mints to results
                results[2].extend(events['burns']) # Add burns to results
                results[3].extend(events['collects']) # Add collects to results
                results[4].extend(events['flashs']) # Add flashs to results
                
            self.logger.debug(f"Processed {len(results[0])} swaps, {len(results[1])} mints, {len(results[2])} collects, {len(results[3])} burns, {len(results[4])} flashs for a total of {len(results[0]) + len(results[1]) + len(results[2]) + len(results[3]) + len(results[4])} events.")
        except Exception as e:
            self.logger.error(f"Error processing bulk responseson : {str(e)}", exc_info=True)
            raise e
        
        return results

    def process_response(self, transaction_data: Dict[str, Any]) -> Dict:
        
        # Create base transaction
        transaction = BaseTransaction(
            id=transaction_data['id'],
            dex_id=self.dex_id,
            block_number=int(transaction_data['blockNumber']),
            timestamp=int(transaction_data['timestamp']),
            gas_used=transaction_data['gasUsed'],
            gas_price=transaction_data['gasPrice']
        )
        
        #self.logger.debug(f"Processing transaction {transaction.id} from block {transaction.block_number}")
        
        # Process events
        events = {
            'swaps': self._process_swaps(transaction_data.get('swaps', []), transaction),
            'mints': self._process_mints(transaction_data.get('mints', []), transaction),
            'burns': self._process_burns(transaction_data.get('burns', []), transaction),
            'collects': self._process_collects(transaction_data.get('collects', []), transaction),
            'flashs': self._process_flashs(transaction_data.get('flashed', []), transaction)
        }
        #self.logger.debug(f"Processed events for transaction {transaction.id}: "
        #                    f"swaps={len(events['swaps'])}, mints={len(events['mints'])}, "
        #                    f"burns={len(events['burns'])}, collects={len(events['collects'])}, "
        #                    f"flashs={len(events['flashs'])}")
        
        return events
    
    def _process_swaps(self, swaps_data: List[Dict], transaction: BaseTransaction) -> List[SwapEvent]:
        
        # Check if there are any swap transactions, check for none
        if not len(swaps_data) > 0:
            #self.logger.debug(f"No swap events found for transaction {transaction.id}")
            return []
        try:
            # Get info from the swap transaction
            swap_transactions = []
            for swap in swaps_data:
                swap_transaction = SwapEvent(
                    parent_transaction = transaction,
                    timestamp = transaction.timestamp,
                    id = swap['id'],
                    token0_symbol = swap['pool']['token0']['symbol'],
                    token1_symbol = swap['pool']['token1']['symbol'],
                    token0_name = swap['pool']['token0']['name'],
                    token1_name = swap['pool']['token1']['name'],
                    token0_id = swap['pool']['token0']['id'],
                    token1_id = swap['pool']['token1']['id'],
                    amount0 = swap['amount0'],
                    amount1 = swap['amount1'],
                    amount_usd = swap['amountUSD'],
                    sender = swap['sender'],
                    recipient = swap['recipient'],
                    origin = swap['origin'],
                    fee_tier = swap['pool']['feeTier'],
                    liquidity = swap['pool']['liquidity'],
                    dex_id = self.dex_id
                )
                swap_transactions.append(swap_transaction)
                #self.logger.debug(f"Processed swap event {swap['id']} for transaction {transaction.id}")
                
            #self.logger.debug(f"Processed {len(swap_transactions)} swap events for transaction {transaction.id}")
        except Exception as e:
            self.logger.error(f"Error processing swap events for transaction {transaction.id}: {str(e)}", exc_info=True)
            raise e
        
        return swap_transactions
    
    def _process_mints(self, mints_data: List[Dict], transaction: BaseTransaction) -> List[MintEvent]:
        
        # Check if there are any mint transactions, check for none
        if not len(mints_data) > 0:
            #self.logger.debug(f"No mint events found for transaction {transaction.id}")
            return []
        
        try:
            mint_transactions = []
            for mint in mints_data:
                mint_transaction = MintEvent(
                    parent_transaction = transaction,
                    timestamp = transaction.timestamp,
                    id = mint['id'],
                    token0_symbol = mint['pool']['token0']['symbol'],
                    token1_symbol = mint['pool']['token1']['symbol'],
                    token0_name = mint['pool']['token0']['name'],
                    token1_name = mint['pool']['token1']['name'],
                    token0_id = mint['pool']['token0']['id'],
                    token1_id = mint['pool']['token1']['id'],
                    amount0 = mint['amount0'],
                    amount1 = mint['amount1'],
                    amount_usd = mint['amountUSD'],
                    owner = mint['owner'],
                    origin = mint['origin'],
                    fee_tier = mint['pool']['feeTier'],
                    liquidity = mint['pool']['liquidity'],
                    dex_id = self.dex_id
                )
                mint_transactions.append(mint_transaction)
                #self.logger.debug(f"Processed mint event {mint['id']} for transaction {transaction.id}")
                
            self.logger.debug(f"Processed {len(mint_transactions)} mint events for transaction {transaction.id}")
        except Exception as e:
            self.logger.error(f"Error processing mint events for transaction {transaction.id}: {str(e)}", exc_info=True)
            raise e
        
        return mint_transactions

    def _process_burns(self, burns_data: List[Dict], transaction: BaseTransaction) -> List[BurnEvent]:
        
        # Check if there are any burn transactions, check for none
        if not len(burns_data) > 0:
            #self.logger.debug(f"No burn events found for transaction {transaction.id}")
            return []
        
        try:
            burn_transactions = []
            for burn in burns_data:
                burn_transaction = BurnEvent(
                    parent_transaction = transaction,
                    timestamp = transaction.timestamp,
                    id = burn['id'],
                    token0_symbol = burn['pool']['token0']['symbol'],
                    token1_symbol = burn['pool']['token1']['symbol'],
                    token0_id = burn['pool']['token0']['id'],
                    token1_id = burn['pool']['token1']['id'],
                    token0_name = burn['pool']['token0']['name'],
                    token1_name = burn['pool']['token1']['name'],
                    amount0 = burn['amount0'],
                    amount1 = burn['amount1'],
                    amount_usd = burn['amountUSD'],
                    owner = burn['owner'],
                    origin = burn['origin'],
                    fee_tier = burn['pool']['feeTier'],
                    liquidity = burn['pool']['liquidity'],
                    dex_id = self.dex_id
                )
                burn_transactions.append(burn_transaction)
                #self.logger.debug(f"Processed burn event {burn['id']} for transaction {transaction.id}")
                
            self.logger.debug(f"Processed {len(burn_transactions)} burn events for transaction {transaction.id}")
        except Exception as e:
            self.logger.error(f"Error processing burn events for transaction {transaction.id}: {str(e)}", exc_info=True)
            raise e
        
        return burn_transactions
    
    def _process_collects(self, collects_data: List[Dict], transaction: BaseTransaction) -> List[CollectEvent]:
        
        # Check if there are any collect transactions, check for none
        if not len(collects_data) > 0:
            #self.logger.debug(f"No collect events found for transaction {transaction.id}")
            return []
        
        try:
            collect_transactions = []
            for collect in collects_data:
                collect_transaction = CollectEvent(
                    parent_transaction = transaction,
                    **collect
                )
                collect_transactions.append(collect_transaction)
                #self.logger.debug(f"Processed collect event {collect['id']} for transaction {transaction.id}")
                
            self.logger.debug(f"Processed {len(collect_transactions)} collect events for transaction {transaction.id}")
        except Exception as e:
            self.logger.error(f"Error processing collect events for transaction {transaction.id}: {str(e)}", exc_info=True)
            raise e
        
        return collect_transactions
    
    
    def _process_flashs(self, flashs_data: List[Dict], transaction: BaseTransaction) -> List[FlashEvent]:
        
        # Check if there are any flash transactions, check for none
        if not len(flashs_data) > 0:
            #self.logger.debug(f"No flash events found for transaction {transaction.id}")
            return []
        
        try:
            flash_transactions = []
            for flash in flashs_data:
                flash_transaction = FlashEvent(
                    parent_transaction = transaction,
                    **flash
                )
                flash_transactions.append(flash_transaction)
                #self.logger.debug(f"Processed flash event {flash['id']} for transaction {transaction.id}")
                
            self.logger.debug(f"Processed {len(flash_transactions)} flash events for transaction {transaction.id}")
        except Exception as e:
            self.logger.error(f"Error processing flash events for transaction {transaction.id}: {str(e)}", exc_info=True)
            raise e
        
        return flash_transactions
    
    def _process_tokens(self, tokens_data: List[Dict]) -> List[Tuple]:
        try:
            tokens = [
                (
                    token['id'],
                    token['symbol'],
                    token['name']
                )
                for token in tokens_data.get("data", {}).get("tokens", [])
            ]  
            self.logger.debug(f"Processed {len(tokens)} tokens")
        except Exception as e:
            self.logger.error(f"Error processing tokens: {str(e)}", exc_info=True)
            raise e
        
        return tokens


